include {
    "stdlib.sw"
}

int TOKENS_INIT_CAP = 256




struct Token {
    ptr char token,
    ptr char file,
    int token_len,
    int line,
    int row,
}

struct TokenList {
    ptr Token tokens,
    int size,
    int capacity,
    int index,
}




func TokenList init_token_list() {
    TokenList list;
    list.size = 0;
    list.index = 0;
    list.capacity = TOKENS_INIT_CAP;
    list.tokens = malloc(list.capacity * sizeof(Token));
    list;
}

func void add_token(ptr TokenList list, ptr char file, int line, int pos, ptr char token) {
    if (list.size >= list.capacity) {
        list.capacity = list.capacity * 2;
        if !(list.capacity) {
            list.capacity = TOKENS_INIT_CAP;
        };
        list.tokens = realloc(list.tokens, list.capacity*sizeof(Token));
    };
    list.tokens[list.size].token = strdup(token);
    list.tokens[list.size].token_len = strlen(token);
    list.tokens[list.size].file = file;
    list.tokens[list.size].line = line;
    list.tokens[list.size].row = pos;
    *list.size++;
}

func void free_token_list(ptr TokenList list) {
    for (i=0, i<list.size, i++, {
        free(list.tokens[i].token);
    });
    free(list.tokens);
    free(list);
}

func int tokenize_string_literal(ptr char str, ptr int pos, ptr int row, ptr char token) {
    quote = str[*pos];
    start = *pos;
    ++(*pos);
    ++(*row);
    i=0;
    token[i++] = *"\"";

    while (str[*pos] != quote && str[*pos] != 0) {
        if (str[*pos] == *"\\") {
            ++(*pos);
            ++(*row);

            if      str[*pos] == *"n"  token[i++] = *"\n"
            else if str[*pos] == *"t"  token[i++] = *"\t"
            else if str[*pos] == *"r"  token[i++] = *"\r"
            else if str[*pos] == *"\\" token[i++] = *"\\"
            else if str[*pos] == *"\"" token[i++] = *"\""
            else if str[*pos] == *"0"  token[i++] = 0
            else {
                token[i++] = *"\\";
                token[i++] = str[*pos];
            };
            ++(*pos);
            ++(*row);
        } else {
            token[i++] = str[*pos];
            ++(*pos);
            ++(*row);
        };
    };

    if str[*pos] == quote {
        token[i++] = *"\"";
        token[i] = 0;
        ++(*pos);
        ++(*row);
        return 1;
    };

    return 0;
}

func ptr TokenList tokenize(ptr char file, ptr char filename) {
    list = alloca(TokenList);
    *list = init_token_list();

    len = strlen(file);
    line = 1; pos = 0; row = 0;
    start_row = 0;
    start_pos = 0;
    reserve 256 as token;

    while pos < len {
        # printf("isalnum = %i\n", isspace(file[pos]));

        if isspace(file[pos]) {
            if (file[pos] == *"\n") {
                line++;
                row = 0;
                # add_token(list, filename, line-1, row, "__EOL__");
            };
            pos++;
            row++;
            continue;

        } else if file[pos] == *"\"" || file[pos] == *"\'" {
            start_row = row;
            if (tokenize_string_literal(file, &pos, &row, token)) {
                add_token(list, filename, line, start_row, token);
                continue;
            } else {
                printf("Error: unmatched quote at %s:%zu:%zu\n", filename, line, pos);
                break;
            };

        } else if isalnum(file[pos]) || file[pos] == *"_" {
            start_pos = pos;
            i = 0;
            start_row = row;
            while (isalnum(file[pos]) || file[pos] == *"_") {
                token[i++] = file[pos];
                pos++;
                row++;
            };
            token[i] = 0;
            add_token(list, filename, line, start_row, token);
            continue;

        } else {
            start_pos = pos;
            token[0] = file[pos];
            token[1] = 0;
            add_token(list, filename, line, row, token);
            pos++;
            row++;
            continue;
        };

        printf("Error: unknown character '%c' at %s:%zu:%zu\n", file[pos], filename, line, pos);
        pos++;
        row++;
    };

    # add_token(list, filename, line, 0, "__EOF__");

    return list;
}

func Token current(ptr TokenList ls) {
    return ls.tokens[ls.index];
}

func Token consume(ptr TokenList ls) {
    return ls.tokens[*ls.index++];
}

func Token peek(ptr TokenList ls) {
    return ls.tokens[ls.index+1];
}

func int more(ptr TokenList ls) {
    return ls.size - ls.index;
}

func bool expect(ptr TokenList ls, ptr char goal) {
    tk = consume(ls);
    match = streq(goal, tk.token);
    if !match {
        printf("ERROR: %s:%zu:%zu expected '%s' but got '%s'\n",
            tk.file,
            tk.row,
            tk.line,
            goal,
            tk.token
        );
        return 0;
    };
    return 1;
}

macro prepend_minus(str) {{
    _len = strlen(str);
    (str) = realloc((str), _len+2);
    memmove((str)+1, (str), _len+1);
    (str)[0] = *"-";
};}


