extern ptr void malloc(int)

extern ptr void realloc(ptr void, int)

extern void free(ptr void)
extern void exit(int)

extern int strlen(ptr char)
extern void strcpy(ptr char, ptr char)
extern ptr char strstr(ptr char, ptr char)
extern int strcmp(ptr char, ptr char)
macro streq(sstr, ssstr) { strcmp(sstr, ssstr) == 0; }

extern int vsnprintf(ptr void, ptr char, ptr char, ptr void)
extern int snprintf(ptr void, ptr char, ptr char, <>)
extern int printf(ptr char, <>)
extern int fprintf(ptr void, ptr char, <>)

extern void write(int, ptr char, int)
extern int read(int, ptr char, int)

macro for(decl, cond, inc, body) {{
    decl;
    while (cond) { body; inc; };
};}

macro TODO(__random_shit) {
    error "Not implemented yet."
}

macro salloc(size) {{
    reserve size as __stack_alloced;
    __stack_alloced;
};}

ptr void nullptr = 0
ptr void NULL = 0
bool true = 1
bool false = 0

extern ptr void memcpy(ptr void, ptr void, int)

struct String {
    ptr char items,
    int length,
    int capacity,
}

struct String_vec {
    ptr String items,
    int length,
    int capacity,
}

func int max(int a, int b) {
    if a > b return a;
    return b;
}

macro _load(ptr) { ptr[0]; }

macro op_ptr(p1, op, p2) { cast cast p1 as int op cast p2 as int as ptr void; }

macro addptr(__p__, __offset__) { op_ptr(__p__, +, __offset__); }

func bool is_letter(char letter) {
    return (letter >= 65 && letter <= 90) || (letter >= 97 || letter <= 122);
}

func bool is_space(char letter) {
    if letter == 10 || letter == 32 || letter == 13 || letter == 9 {
        return true;
    } else {
        return false;
    };
    return false;
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
	made.items = NULL;
	return made;
}

macro cstr(str_name) { (str_name).items; }

macro copy(__str) { SS(cstr(__str)); }

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
    if _str.length+1 >= _str.capacity {
        _str.items = realloc(_str.items, _str.capacity*2);
        _str.capacity = _str.capacity*2;
    };
    int inserted = 0;
    char old;
    for(int idx=0, idx < _str.length+1, idx++, {
        old = _str.items[idx]; 
        if idx == _pos {
            inserted++;
            _str.items[idx] = _new;
        };
        _str.items[idx+inserted] = old;
    });
    _str.length = _str.length+1;
    return;
}

func void str_add(ptr String str, ptr char _new) {
    str_insert(str, str.length, _new); return;
}

func void str_add_char(ptr String str, char _new) {
    str_insert_char(str, str.length, _new); return;
}

func void str_free(ptr String str) {
    str.length = 0;
    str.capacity = 0;
    free(str.items);
    return;
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

func String str_substr(String str, int pos, int end) {
    int len = end-pos;
    String buf;
    buf.capacity = len+1;
    buf.length = len;
    buf.items = malloc(len+1);
    
    memcpy(buf.items, addptr(str.items, pos), len+1);
    buf.items[len] = 0;
    return buf;
}

func void str_lstrip(ptr String str) {
    int pos = 0;
    for(int i = 0, i < *str.length, ++i, {
        if is_space(*str.items[i]) {
            pos++;
        } else {
            if pos {
                String old_str = *str;
                *str = str_substr(old_str, pos, old_str.length+1);
                str_free(&old_str);
                return;
            } else { return; };
        };
    });
    return;
}

func bool cstr_is_space(ptr char _str) {
    int length = strlen(_str);
    for(int i = 0, i < length, ++i, {
        if !(is_space(_str[i])) {
            return false;
        };
    });
    return true;
} 

func void str_clear(ptr String _str) { _str.length = 0; *(_str.items) = 0; return; }

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
    made.items = NULL;
    made.capacity = 0;
    return made;
}

func void str_vec_append(ptr String_vec _vec, String _str) {
    String_vec vec = *_vec;
    if (vec.length+1 >= vec.capacity) {
        int old_cap = vec.capacity;
        vec.capacity = vec.capacity * 2;
        if !(vec.capacity) {
            vec.capacity = 1;
        };
        vec.items = realloc(vec.items, sizeof(String)*vec.capacity);
    };
    vec.items[vec.length++] = _str;
    *_vec = vec;
    return;
}

func String str_copy(String _str) {
    return str_substr(_str, 0, _str.length);
}

func String_vec str_split(String _str, char c) {
    String_vec vtemp = str_vec_init();
    int found = -1;
    String temp;
    int len = _str.length;
    for (int idx=0, idx < len, idx++, {
        if _str.items[idx] == c {
            temp = str_substr(_str, found+1, idx);
            found = idx;
            str_vec_append(&vtemp, temp);
        };
    });
    str_vec_append(&vtemp, str_substr(_str, found+1, _str.length));
    return vtemp;
}

macro cstr_fmt(__fmt__, __args__) {{
    int __size__ = snprintf(NULL, 0, __fmt__, __args__);
    ptr char __str__ = malloc(__size__+1);
    snprintf(__str__, __size__+1, __fmt__, __args__);
    __str__;
};}

func void __write_and_free(int fp, ptr char str) { write(fp, str, strlen(str)); free(str); }

macro eprintf(__str__, __fmt__) {
    __write_and_free(2, cstr_fmt (__str__, __fmt__) );
}

macro str_fmt(__str, __fmt) {
    ptr char __cstr__ = cstr_fmt((__str).items, [__fmt]);
    str_free(&(__str));
    __str = SS(__cstr__);
    __str;
}

