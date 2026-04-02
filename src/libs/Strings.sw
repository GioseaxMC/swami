
struct String {
    ptr char items,
    int length,
    int capacity,
}

struct StringVec {
    ptr String items,
    int length,
    int capacity,
}

macro _str_da_end(__da) { _op_ptr((__da.items),+,sizeof(*(__da).items)*(__da).length); }

macro _str_foreach(__da, __iter_n, __body) {{
    for(__iter_n = (__da).items, _op_ptr(__iter_n,!=,_str_da_end(__da)), __iter_n=__iter_n+sizeof(*(__da.items)), __body);
};}

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
    if (!(cond)) { printf("ASSERT: %s", message); exit(-1); };
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
    for(int i = 0, i < str.length, ++i, {
        if is_space(str.items[i]) {
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

func StringVec str_vec_init() {
    StringVec made;
    made.length = 0;
    made.items = NULL;
    made.capacity = 0;
    return made;
}

func void str_vec_append(ptr StringVec _vec, String _str) {
    StringVec vec = *_vec;
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

func StringVec str_split(String _str, char c) {
    StringVec vtemp = str_vec_init();
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

macro str_fmt(__str, __fmt) {
    ptr char __cstr__ = cstr_fmt((__str).items, [__fmt]);
    str_free(&(__str));
    __str = SS(__cstr__);
    __str;
}
