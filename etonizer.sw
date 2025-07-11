include {
    "stdlib.sw"
}




struct Token {
    ptr char token,
    ptr char file,
    int token_len,
    int line,
    int pos,
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
    list.capacity = 0;
    list.tokens = malloc(list.capacity * sizeof(Token));
    list;
}

func void add_token(ptr TokenList list, ptr char file, int line, int pos, ptr char token) {
    if (list.size >= list.capacity) {
        list.capacity = list.capacity * 2;
        list.tokens = realloc(list.tokens, list.capacity*sizeof(Token));
    };
    list.tokens[list.size].token = strdup(token);
    list.tokens[list.size].token_len = strlen(token);
    list.tokens[list.size].file = file;
    list.tokens[list.size].line = line;
    list.tokens[list.size].pos = pos;
    *list.size++;
}

func void free_token_list(ptr TokenList list) {
    for (i=0, i<list.size, i++, {
        free(list.tokens[i].token);
    });
    free(list.tokens);
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
            else if str[*pos] == *"\\" token[i++] = *"\\"
            else if str[*pos] == *"\"" token[i++] = *"\""
            else if str[*pos] == *"0"  token[i++] = 0
            else {
                token[i++] = *"\\";
                token[i++] = str[*pos];
            };
        } else {
            token[i++] = str[*pos];
            ++(*pos);
            ++(*pos);
        };
    };
}

func void main() {}
