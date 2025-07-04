struct Alexer_String_Builder {
    ptr char items,
    int count,
    int capacity,
}

int ALEXER_DA_INIT_CAP = 256

macro alexer_assert(cond, message) {
    if (!cond) printf("%s \n", message);
}

macro alexer_da_append_many(da, new_items, new_items_count) {{
    if ((da).count + (new_items_count) > (da).capacity) {
        if (da).capacity == 0 {
            (da).capacity = ALEXER_DA_INIT_CAP;
        };
        while (da).count + (new_items_count) > (da).capacity {
            (da).capacity = (da).capacity * 2;
        };
        (da).items = realloc((da).items, (da).capacity*sizeof(*(da).items));
        alexer_assert((da).items != NULL, "Buy more RAM lol");
    };
    memcpy(op_ptr((da).items, +, (da).count), (new_items), (new_items_count)*sizeof(*(da).items));
    (da).count = (da).count + (new_items_count);
}}

macro alexer_sb_append_cstr(sb, cstr) {{
    s = (cstr);
    n = strlen(s);
alexer_da_append_many(sb, s, n);
}}

macro alexer_sb_append_null(sb) {
    alexer_sb_append_many(sb, "", 1);
}

struct Alexer_Loc {
    ptr char file_path,
    int row,
    int col,
}

int ALEXER_INVALID = 0
int ALEXER_END = 1
int ALEXER_INT = 2
int ALEXER_SYMBOL = 3
int ALEXER_KEYWORD = 4
int ALEXER_PUNCT = 5
int ALEXER_STRING = 6
int ALEXER_COUNT_KINDS = 7

ptr char alexer_kind_names
func void init_names() {
    alexer_kind_names = malloc(alexer_kind_names * sizeof(ptr char));
    alexer_kind_names[ALEXER_INVALID] = "INVALID";
    alexer_kind_names[ALEXER_END] = "END";
    alexer_kind_names[ALEXER_INT] = "INT";
    alexer_kind_names[ALEXER_SYMBOL] = "SYMBOL";
    alexer_kind_names[ALEXER_KEYWORD] = "KEYWORD";
    alexer_kind_names[ALEXER_PUNCT] = "PUNCT";
    alexer_kind_names[ALEXER_STRING] = "STRING";
}

macro alexer_kind_name(kind) {
    alexer_assert(kind < ALEXER_COUNT_KINDS, "Invalid count");
    alexer_kind_names[kind];
}

struct Alexer_Token {
    int id,
    Alexer_loc loc,
    ptr char begin,
    ptr char end,
    int int_value,
}

func bool alexer_token_text_equal(Alexer_Token a, Alexer_token b) {
    na = cast op_ptr(a.end, -, a.begin) as int;
    nb = cast op_ptr(b.end, -, b.begin) as int;
    if na!=nb return false;
    memcmp(a.begin, b.begin, na) == 0;
}

func bool alexer_token_text_equal_cstr(Alexer_Token a, ptr char b) {
    na = cast op_ptr(a.end, -, a.begin) as int;
    nb = cast op_ptr(b.end, -, a.begin) as int;
    if (na!=nb) return false;
    memcmp(a.begin, b, na) == 0;
}

struct Alexer_ML_Comments {
    ptr char opening,
    ptr char closing,
}

struct Alexer_state {
    int cur,
    int bol,
    int row,
}

func Alexer_state alexer_save(ptr Alexer l) {
    Alexer_State = s;
    s.cur = l.cur;
    s.bol = l.bol;
    s.row = l.row;
    return s;
}

func void alexer_rewind(ptr Alexer l, Alexer_State s) {
    l.cur = s.cur;
    l.bol = s.bol;
    l.row = s.row;
}:

struct Alexer {
    ptr char file_path,
    ptr char content,
    int size,

    int cur,
    int bol,
    int row,

    ptr ptr char puncts,
    int puntcs_count,
    ptr ptr char keywords,
    int keywords_count,
    ptr ptr char sl_comments,
    int sl_comments_count,
    Alexer_ML_Comments ml_contents,
}
