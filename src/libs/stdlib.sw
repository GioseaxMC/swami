extern ptr void malloc(int)

extern ptr void realloc(ptr void, int)

extern void free(ptr void)
extern void exit(int)

extern int strlen(ptr char)
extern void strcpy(ptr char, ptr char)
extern ptr char strstr(ptr char, ptr char)
extern int strcmp(ptr char, ptr char)
extern void va_start(ptr void)
extern void va_end(ptr void)
extern int vsnprintf(ptr void, ptr char, ptr char, ptr void)

extern void printf(ptr char, <>)

macro streq(sstr, ssstr) { strcmp(sstr, ssstr) == 0; }

macro for(decl, cond, inc, body) {{
    decl;
    while (cond) {body; inc; };
};}

ptr void nullptr = 0

ptr void NULL = 0

extern ptr void memcpy(ptr void, ptr void, int)

struct String {
    ptr char items,
    int capacity,
    int length,
}

struct String_vec {
    ptr String items,
    int length,
    int capacity,
}

macro _load(ptr) { ptr[0]; }

macro addptr(p, offset) { cast offset + cast p as int as ptr void; }

func bool is_letter(char letter) {
    return (letter >= 65 && letter <= 90) || (letter >= 97 || letter <= 122);
}


macro str_assert(cond, message) {
    if (!cond) { printf("ASSERT: %s", message); exit(0-1); };
}

func int next_powt(int len) {
    int temp = 1;
    while (temp <= len) {
        temp = temp * 2;
    };
    return temp;
}

func String str_init() {
    String made;
	made.length = 0;
	made.capacity = 0;
	made.items = malloc(0);
	return made;
}

macro c(str_name) { (str_name).items; }

func void str_set(ptr String _str, ptr char other) {
	String str = *_str;
    int other_length = strlen(other);
	str.capacity = next_powt(other_length);
	ptr char old_items = str.items;
	str.items = malloc(str.capacity);
    strcpy(str.items, other);
    str.length = other_length;
    if (old_items) free(old_items);
    *_str = str;
    return;
}

macro str_make(str_name, str_contents) {
    {
        String str_name = str_init();
        str_set(&str_name, str_contents);
    };
}

func String SS(ptr char string) {
    str_make(__str__, string);
    return __str__;
}

func void str_insert(ptr String _str, int _pos, ptr char _new) {
    String str = *_str;
    ptr char old_items = str.items;
    int new_len = strlen(_new);
    str.capacity = next_powt(str.length + strlen(_new));
    str.items = malloc(str.capacity);
    int inserted = 0;
    int idx = 0;
    while (str.length+1 > idx) {
        if (idx == _pos) {
            while (new_len > inserted) {
                str.items[idx+inserted] = _new[inserted];
                inserted++;
            };
        };
        str.items[idx+inserted] = old_items[idx];
        idx++;
    };
    str.length = str.length + new_len;
    str.items[str.length] = 0;
    if (old_items) free(old_items);
    *_str = str;
    return;
}

func void str_insert_char(ptr String _str, int _pos, char _new) {
    String str = *_str;
    ptr char old_items = str.items;
    int new_len = 1;
    str.capacity = next_powt(str.length + 1);
    str.items = malloc(str.capacity);
    int idx = 0;
    while (str.length+1 > idx) {
        if (idx == _pos) {
            str.items[idx] = _new;
        };
        str.items[idx+1] = old_items[idx];
        idx++;
    };
    str.length = str.length + new_len;
    str.items[str.length] = 0;
    if (old_items) free(old_items);
    *_str = str;
    return;
}

func void str_add(ptr String str, ptr char _new) {
    str_insert(str, str.length, _new); return;
}

func void str_add_char(ptr String str, char _new) {
    str_insert_char(str, str.length, _new); return;
}

func void str_remove(ptr String _str, int _pos, int _len) {
    String str = *_str;
    str_assert((_len > 0), "length of remover must be more than 0");
    str_assert((_len+_pos <= str.length), "removing out of range");
    int idx = 0;
    while (str.length-_pos-_len+1 > idx) {
        if (_pos+idx+_len <= str.length) {
            str.items[_pos+idx] = str.items[_pos+idx+_len];
        };
        idx++;
    };
    str.length = str.length - _len;
    *_str = str;
    return;
}

func void str_free(ptr String _str) {
    String str = *_str;
    str.length = 0;
    str.capacity = 1;
    free(str.items);
    str.items = malloc(1);
    str.items[0] = 0;
    *_str = str;
    return;
}

func void str_clear(ptr String _str) { _str.length = 0; return; }

func void str_replace(ptr String _str, ptr char _old, ptr char _new) {
    String str = *_str;
    int old_len = strlen(_old);
    int new_len = strlen(_new);
    ptr char result;
    int offset = 0;
    while !((result = strstr(addptr(str.items, offset), _old)) == NULL) {
        int _pos = cast result as int - cast str.items as int;
        str_remove(&str, _pos, old_len);
        int middle = cast result as int + new_len - cast str.items as int;
        offset = middle;
        str_insert(&str, _pos, _new);
    };
    *_str = str;
    return;
}

func String_vec str_vec_init() {
    String_vec made;
    made.length = 0;
    made.items = malloc(0);
    made.capacity = 0;
    return made;
}

func void str_vec_append(ptr String_vec _vec, String _str) {
    String_vec vec = *_vec;
    if (vec.capacity <= (vec.length+1)) {
        vec.capacity = vec.capacity * 2;
        if !(vec.capacity) {
            vec.capacity = 1;
        };
        ptr String new_items = malloc(sizeof(String)+1);
        memcpy(new_items, vec.items, vec.capacity);
        free(vec.items);
    };
    vec.length++;
    vec.items[vec.length] = _str;
    *_vec = vec;
    return;
}

func String_vec str_split(ptr String _str, char c) {
    int idx = 0;
    String_vec vtemp = str_vec_init();
    String temp = str_init();
    for (int idx=0, idx < (*_str.length), idx++, {
        if (_str.items[idx] == c) {
            str_vec_append(&vtemp, temp);
            str_clear(&temp);
        } else {
            str_add_char(&temp, *_str.items[idx]);
        };
    });
    str_vec_append(&vtemp, temp);
    return vtemp;
}

func ptr char cstr_fmt(ptr char fmt, <>) {
    ptr void args;
    va_start(&args);

    int size = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    
    if (size < 0) return NULL;
    
    ptr char buffer = malloc(size + 1);
    if (!buffer) return NULL;
    
    va_start(&args);

    vsnprintf(buffer, size + 1, fmt, args);
    va_end(args);

    return buffer;
}

func void str_fmt(ptr String fmt, <>) {
    ptr char to_free = fmt.items;
    fmt.items = cstr_fmt(fmt.items);
    free(to_free);
    return;
}
