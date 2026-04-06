include {
    "etonizer.sw",
    "stdlib.sw",
    "darrays.sw",
    "dicts.sw"
}

#js_get_int(js, "number");
#js_get_str(js, "string");
#js_get_json(js, "object");
#js_get_array(js, "array");

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
    ptr void arr,
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
    while t=current(tokens).token[0] != *"}" {
        if current(tokens).token[0] != *"\"" return json_error(*current(tokens));
        key = get_string(*consume(tokens));
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
        j.str = get_string(*consume(tokens));
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
    js__parse_primary(tokens);
}

func ptr Json json_get(Json _j, ptr char query) {
    ptr Json j = &_j;
    tokens = tokenize(query, "<json_query>");
    while t=consume(tokens) {
        if t.token[0] == *"[" {
            idx = atoi(consume(tokens).token);
            expect(tokens, "]");
            j = & (cast j.arr as ptr Json [idx]);
        } else {
            dict = j.dict;
            j = ht_get(dict, t.token);
        };
    };
    return j;
}


