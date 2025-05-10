extern ptr void malloc(int)

extern ptr void realloc(ptr void, int)

extern ptr void fopen(ptr void, ptr char)

extern int rewind(ptr void)
extern int fseek(ptr void, int, int)
extern int ftell(ptr void)
extern int fclose(ptr void)
extern int fwrite(ptr char, int, int, ptr void)
extern int fread(ptr void, int, int, ptr void)

extern void free(ptr void)
extern void exit(int)

extern int strlen(ptr char)
extern void strcpy(ptr char, ptr char)
extern ptr char strstr(ptr char, ptr char)
extern void va_start(ptr void)
extern void va_end(ptr void)
extern int vsnprintf(ptr void, ptr char, ptr char, ptr void)

extern void printf(ptr char, <>)

ptr void nullptr = 0

int sizeof_string = 24

ptr void str_null = 0

func int write_file(ptr char filename, ptr char contents) {
    ptr void file = fopen(filename, "wb");
    if (!(file == nullptr)) {
        printf("Error opening file\n");
        fclose(file); 
        return -1;
    };
    
    int len = strlen(contents);
    int written = fwrite(contents, 1, len, file);
    
    if (!(written == len)) {
        printf("Error writing to file");
        fclose(file);
        return -1;
    };
    
    fclose(file);
    return 0;
}

func ptr char read_file(ptr char filename, ptr int size) {
    ptr void file = fopen(filename, "rb");
    if (!file) return nullptr;

    fseek(file, 0, 2);
    size[0] = ftell(file);
    rewind(file);

    ptr char buffer = malloc(size[0]+1);
    if !buffer { fclose(file); return nullptr; };

    fread(buffer, 1, size[0], file);
    buffer[size[0]] = 0;

    fclose(file);
    return buffer;
}

extern ptr void memcpy(ptr void, ptr void, int)

struct string {
    ptr char data,
    int capacity,
    int length,
}

struct string_vec {
    ptr string items,
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

func string str_init() {
    string made;
	made.length = 0;
	made.capacity = 0;
	made.data = malloc(0);
	return made;
}

macro str_make(str_name, str_contents) {
    {
        string str_name = str_init();
        str_set(&str_name, str_contents);
    };
}

macro c(str_name) { str_name.data; }

func void str_set(ptr string _str, ptr char other) {
	string str = _str[0];
    int other_length = strlen(other);
	str.capacity = next_powt(other_length);
	ptr char old_data = str.data;
	str.data = malloc(str.capacity);
    strcpy(str.data, other);
    str.length = other_length;
    if (old_data) free(old_data);
    _str[0] = str;
    return;
}

func void str_insert(ptr string _str, int _pos, ptr char _new) {
    string str = _str[0];
    ptr char old_data = str.data;
    int new_len = strlen(_new);
    str.capacity = next_powt(str.length + strlen(_new));
    str.data = malloc(str.capacity);
    int inserted = 0;
    int idx = 0;
    while (str.length+1 > idx) {

        if (idx == _pos) {
    
            while (new_len > inserted) {
        
                str.data[idx+inserted] = _new[inserted];
        
                inserted++;
        
            };
    
        };

        str.data[idx+inserted] = old_data[idx];

        idx++;
    };
    str.length = str.length + new_len;
    str.data[str.length] = 0;
    if (old_data) free(old_data);
    _str[0] = str;
    return;
}

func void str_add(ptr string _str, ptr char _new) {
    string str = _str[0];
    str_insert(&str, str.length, _new);
    _str[0] = str;
    return;
}

func void str_remove(ptr string _str, int _pos, int _len) {
    string str = _str[0];
    str_assert((_len > 0), "length of remover must be more than 0");
    str_assert((_len+_pos <= str.length), "removing out of range");
    int idx = 0;
    while (str.length-_pos-_len+1 > idx) {
        if (_pos+idx+_len <= str.length) {
            str.data[_pos+idx] = str.data[_pos+idx+_len];
        };
        idx++;
    };
    str.length = str.length - _len;
    _str[0] = str;
    return;
}

func void str_clear(ptr string _str) {
    string str = _str[0];
    str.length = 0;
    str.capacity = 1;
    free(str.data);
    str.data = malloc(1);
    str.data[0] = ""[0];
    _str[0] = str;
    return;
}

func void str_replace(ptr string _str, ptr char _old, ptr char _new) {
    string str = _load(_str);
    int old_len = strlen(_old);
    int new_len = strlen(_new);
    ptr char result;
    int offset = 0;
    while !((result = strstr(addptr(str.data, offset), _old)) == str_null) {
        int _pos = cast result as int - cast str.data as int;
        str_remove(&str, _pos, old_len);
        int middle = cast result as int + new_len - cast str.data as int;
        offset = middle;
        str_insert(&str, _pos, _new);
    };
    _str[0] = str;
    return;
}

func string_vec ptr_vec_init() {
    string_vec made;
    made.length = 0;
    made.items = malloc(0);
    made.capacity = 0;
    return made;
}

func void ptr_vec_append(ptr string_vec _vec, string _str) {
    string_vec vec = _vec[0];
    if (vec.capacity <= (vec.length+1)) {
        vec.capacity = vec.capacity * 2;
        if !(vec.capacity) {
            vec.capacity = 1; 
        };
        ptr string new_data = malloc(sizeof_string+1);
        memcpy(new_data, vec.items, vec.capacity);
        free(vec.items);
    };
    vec.length++;
    vec.items[vec.length] = _str;
    _vec[0] = vec;
    return;
}

func string_vec str_split(string _str, char c) {
    int idx = 0;
    string_vec vtemp = ptr_vec_init();
    string temp = str_init();
    while (idx < (_str.length)) {
        if (cast _str.data as char == c) {
            0;
        };
    };
    return vtemp;
}

ptr void NULL = 0

func ptr char str_fmt(ptr char fmt, <>) {
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