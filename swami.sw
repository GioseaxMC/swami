include "stdlib.sw";

int iota_counter = 0;

func int iota(int reset) {
    if (reset != (0-1)) {
        iota_counter++;
    } else if (reset) {
        iota_counter = 0;
    }
    return iota_counter;
}

int DEBUGGING = 0;
int parse_level = 0;
ptr ptr char llvm_type;
ptr ptr char human_type;

func void debug(ptr char arg) {
    if DEBUGGING {
        int idx = 0;
        while (idx < parse_level) {
            print("|  ");
            idx++;
        }
        println(arg);
    }
    return;
}

func ptr char rlt(int type, int ptr_level) {
    string pointer = str_from_cstr(llvm_type[type]);
    int idx = 0;
    while (idx < ptr_level) {
        str_add(&pointer, "*");
        idx++;
    }
    return (pointer.data);
}

func ptr char hlt(int type, int ptr_level) {
    string pointer = str_from_cstr("");
    int idx = 0;
    while (idx < ptr_level) {
        str_add(&pointer, "ptr ");
        idx++;
    }
    str_add(&pointer, human_type[type])
    return (pointer.data);
}

struct token {
    ptr char name;
    int col;
    int row;
    ptr char filename;
}

struct dict {
    ptr char keys;
    ptr void data;
}

struct statement {
    ptr char name;
    int kind;
    int type;
    int ptr_level;
    int subkind;
    ptr statement args;
    statement block;
    ptr char value;
    token ogToken;
    token lastToken;
    dict namespace;
    dict namespace_pevel;
}

func ptr char get_tk_pos(token tk) {
    return str_fmt("%s:%zu:%zu", tk.name, (tk.col+1), (tk.row+1))
}

func void parser_error(token tk, ptr char prompt, int errno) {
    println("%s: ERROR: %s", get_tk_pos(), str_fmt(prompt, token.name))
    content = read_file(token.filename)
    
    return;
}

func void init_stuff() {
    llvm_type = cast(ptr ptr char, malloc(8 * 6));
    llvm_type[0] = "ptr";
    llvm_type[1] = "i64";
    llvm_type[2] = "void";
    llvm_type[3] = "char";
    llvm_type[4] = "i1";
    llvm_type[5] = "...";
    
    human_type = cast(ptr ptr char, malloc(8 * 6));
    human_type[0] = "ptr";
    human_type[1] = "int";
    human_type[2] = "void";
    human_type[3] = "char";
    human_type[4] = "bool";
    human_type[5] = "..";    
    return;
}



func int main(int argc, ptr ptr char argv) {
    init_stuff()
    parser_error()

    return 0;
}