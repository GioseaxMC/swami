include {
    "etonizer.sw",
    "stdlib.sw",
    "darrays.sw",
    "dicts.sw"
}

# this library DOES NOT respect the json standard as of now.
# keys like "foo bar" "<emoji>" or escaped character are not supported

# the strings are not escaped, they are just read as seen.
# the language has not floats, so the json parser does not support them.

# this parser was made for the sole purpose of training myself in implementing
# the swami programming language in itself, testing the tokenizer's capabilities
# and may be improved in the future

enum(
    JSON_NUM,
    JSON_ARR,
    JSON_OBJ,
    JSON_STR
)

struct Json__Generic {
    ptr ptr void dict,
    ptr char str,
    int num,
    ptr void arr,
    int kind,
}

struct Json {
    ptr ptr Json__Generic dict,
    ptr char str,
    int num,
    ptr Json__Generic arr,
    int kind,
}

extern int atoi(ptr char)

func ptr void json_error(Token t) {
    print(t.file, ":", t.line, ":", t.row, " ");
    println("Expected key but got '", t.token, "'");
    return NULL;
}

func ptr ptr Json js__parse_object(ptr TokenList tokens) {
    if !expect(tokens, "{") return NULL;
    dict = new_ht(Json);
    reserve 2048 as key;
    while t=current(tokens).token[0] != *"}" {
        if current(tokens).token[0] != *"\"" return json_error(*current(tokens));
        get_string(key, *consume(tokens));
        expect(tokens, ":");
        Json json = js__parse_primary(tokens);
        *ht_get(dict, key) = json;
        if current(tokens).token[0] != *"}"
            expect(tokens, ",");
    };
    expect(tokens, "}");
    return dict;
}

func ptr Json js__parse_array(ptr TokenList tokens) {
    if !expect(tokens, "[") return NULL;
    arr = new_array(Json);
    while t=current(tokens).token[0] != *"]" {
        arr_push(arr, js__parse_primary(tokens));
        if current(tokens).token[0] != *"]"
            expect(tokens, ",");
    };
    expect(tokens, "]");
    return arr;
}

func Json js__parse_primary(ptr TokenList tokens) {
    Json j;
    t = current(tokens);
    if t.token[0] == *"{" {
        j.dict = js__parse_object(tokens);
        j.kind = JSON_OBJ;
    } else if t.token[0] == *"[" {
        j.arr = js__parse_array(tokens);
        j.kind = JSON_ARR;
    } else if t.token[0] == *"\"" {
        reserve 1024 as str;
        j.str = strdup(get_string(str, *consume(tokens)));
        j.kind = JSON_STR;
    } else {
        j.num = atoi(consume(tokens).token);
        j.kind = JSON_NUM;
    };
    return j;
}


func Json js_parse_string(ptr char contents, ptr char filename)
{
    tokens = tokenize(contents, filename);
    j = js__parse_primary(tokens);
    free_token_list(tokens);
    j;
}

func ptr Json json_get(ptr Json j, ptr char query) {
    if !j return NULL;
    tokens = tokenize(query, "<json_query>");
    while t=consume(tokens) {
        if t.token[0] == *"[" {
            if j.kind != JSON_ARR { j=NULL; break; };
            idx = atoi(consume(tokens).token);
            expect(tokens, "]");
            if !arr_exists(j.arr, idx) { j=NULL; break; };
            j = &(j.arr[idx]);
        } else {
            dict = j.dict;
            if j.kind != JSON_OBJ { j=NULL; break; };
            j = ht_get(dict, t.token);
        };
    };
    free_token_list(tokens);
    return j;
}

# this is just a test, this interface may be better for supporting keys with spaces...
macro json_get_many(json, args) {{
    ptr Json __many_json = json;
    unroll (x) (args) { __many_json = json_get(__many_json, x); };
    __many_json;
};}

func void p_indent(int n) {
    for(i=0, i<n, ++i, print("  "));
}

func void _json_print(ptr Json j, int lvl) {
    nlvl = lvl+1;
    if j.kind == JSON_OBJ {
        println("{");
        ht_foreach(j.dict, _, di, { p_indent(nlvl); print("\"", _, "\" : "); _json_print(di, nlvl); println(","); });
        p_indent(lvl); print("}");
    } else if j.kind == JSON_ARR {
        print("[");
        foreach(j.arr, ai, { _json_print(ai, nlvl); if ai!=&j.arr[arr_len(j.arr)-1] print(", "); });
        print("]");
    } else if j.kind == JSON_NUM {
        print(j.num);
    } else if j.kind == JSON_STR {
        print("\"", j.str, "\"");
    };
}

macro json_print(js) { _json_print(js, 0); printf("\n"); }

func void json_free(ptr Json j) {
    if j.kind == JSON_OBJ {
        ht_foreach(j.dict, _, di, {
            json_free(di);
        });
        ht_free(j.dict); 
    } else if j.kind == JSON_ARR {
        foreach(j.arr, ai, {
            json_free(ai);
        });
        arr_free(j.arr);
    } else if j.kind == JSON_STR {
        free(j.str);
    };
}
