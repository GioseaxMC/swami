struct Alexer_String_Builder {
    ptr char items,
    int count,
    int capacity,
}

ALEXER_DA_INIT_CAP = 256

macro alexer_assert(cond, message) {
    if (!cond) printf("%s \n", message);
}

macro alexer_da_append_many(da, new_items, new_items_count) {{
    if ((da).count + (new_items_count) > (da).capacity) {
        if (da).capacity == 0) {
            (da).capacity = ALEXER_DA_INIT_CAP;
        };
        while (da).count + (new_items_count) > (da).capacity) {
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


