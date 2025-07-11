#ifdef ETONIZER_HANDLE_INCLUDES

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#endif

typedef struct {
    char *token;
    char *file;
    size_t token_len;
    size_t line;
    size_t pos;
} Token;

typedef struct {
    Token *tokens;
    size_t size;
    size_t capacity;
    size_t index;
} TokenList;

#define TK_LO "\x1b[31m%s:\x1b[0m\x1b[33m%zu\x1b[0m:\x1b[32m%zu\x1b[0m"
#define TK_SL "\x1b[31m%s:\x1b[0m\x1b[33m%zu\x1b[0m"

#define tk_locator(tk) (tk).file, (tk).line, (tk).pos

void init_token_list(TokenList *list) {
    list->size = 0;
    list->index = 0;
    list->capacity = 10;
    list->tokens = (Token *)malloc(list->capacity * sizeof(Token));
}

void add_token(TokenList *list, char *file, size_t line, size_t pos, char *token) {
    if (list->size >= list->capacity) {
        list->capacity *= 2;
        list->tokens = (Token *)realloc(list->tokens, list->capacity * sizeof(Token));
    }
    list->tokens[list->size].token = strdup(token);
    list->tokens[list->size].token_len = strlen(token);
    list->tokens[list->size].file = file;
    list->tokens[list->size].line = line;
    list->tokens[list->size].pos = pos;
    list->size++;
}

void free_token_list(TokenList *list) {
    for (size_t i = 0; i < list->size; i++) {
        free(list->tokens[i].token);
    }
    free(list->tokens);
}

int tokenize_string_literal(char *str, size_t *pos, size_t *row, char *token) {
    char quote = str[*pos];
    size_t start = *pos;
    (*pos)++;
    (*row)++;
    size_t i = 0;
    token[i++] = '"';  // Add opening quote

    while (str[*pos] != quote && str[*pos] != '\0') {
        if (str[*pos] == '\\') { // Handle escape sequence
            (*pos)++;
            (*row)++;

            // Check for escape sequences
            switch (str[*pos]) {
                case 'n':
                    token[i++] = '\n';
                    break;
                case 't':
                    token[i++] = '\t';
                    break;
                case '\\':
                    token[i++] = '\\';
                    break;
                case '"':
                    token[i++] = '"';
                    break;
                case '0':
                    token[i++] = 0;
                    break;
                default:
                    token[i++] = '\\'; // Escape backslash if unknown sequence
                    token[i++] = str[*pos];
                    break;
            }
            (*pos)++;
            (*row)++;
        } else {
            token[i++] = str[*pos]; // Normal character
            (*pos)++;
            (*row)++;
        }
    }

    if (str[*pos] == quote) {
        token[i++] = '"';  // Add closing quote
        token[i] = '\0';
        (*pos)++;
        (*row)++;
        return 1;
    }

    return 0;  // Error if no closing quote
}

void tokenize(char *file, TokenList *list, char* filename) {
    size_t len = strlen(file);
    size_t line = 1, pos = 0, row=1;
    char token[256];
    
    while (pos < len) {

        if (isspace(file[pos])) {
            if (file[pos] == '\n') { line++; row=0; add_token(list, filename, line-1, row, "__EOL__");}
            pos++;
            row++;
            continue;
            
        }
        

        if (file[pos] == '"' || file[pos] == '\'') {
            size_t start_row = row;
            if (tokenize_string_literal(file, &pos, &row, token)) {
                add_token(list, filename, line, start_row, token);
                continue;
            }
            else {
                fprintf(stderr, "Error: unmatched quote at line %zu, position %zu\n", line, pos);
                break;
            }
        }


        if (isalnum(file[pos]) || file[pos] == '_') {
            size_t start_pos = pos;
            size_t i = 0;
            size_t start_row = row;
            while (isalnum(file[pos]) || file[pos] == '_') {
                token[i++] = file[pos];
                pos++;
                row++;
            }
            token[i] = '\0';
            add_token(list, filename, line, start_row, token);
            continue;
        }


        else {
            size_t start_pos = pos;
            token[0] = file[pos];
            token[1] = '\0';
            add_token(list, filename, line, row, token);
            pos++;
            row++;
            continue;
        }


        fprintf(stderr, "Error: unknown character '%c' at line %zu, position %zu\n", file[pos], line, pos);
        pos++;
        row++;
    }
    add_token(list, filename, line, 0, "__EOF__");
}

Token current(TokenList* ls) {
    return ls->tokens[ls->index];
}

Token consume(TokenList* ls) {
    return ls->tokens[ls->index++];
}

Token peek(TokenList* ls) {
    return ls->tokens[ls->index+1];
}

int more(TokenList* ls) {
    return ls->size - ls->index;
}

int expect(TokenList* ls, char* goal) {
    Token tk = consume(ls);
    int match = strcmp(goal, tk.token) != 0;
    if (match) {
        printf("ERROR: "TK_LO" Expected '%s' but got '%s'\n", tk_locator(tk), goal, tk.token);
        exit(-1);
    }
    // else {
    //     printf("actually got %s\n", goal);
    // }
    
}

#define PREPEND_MINUS(str)                      \
    do {                                                \
        size_t _len = strlen(str);                      \
        (str) = realloc((str), _len + 2);               \
        memmove((str) + 1, (str), _len + 1);            \
        (str)[0] = '-';                                 \
    } while (0)
