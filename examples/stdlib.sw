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

ptr void nullptr = 0

int sizeof_string = (3 * 8)

func int write_file(ptr char filename, ptr char contents) {
    ptr void file = fopen(filename, "wb");
    if (!(file == nullptr)) {
        printf("Error opening file\n");
        fclose(file); 
        return (0-1);
    };
    
    int len = strlen(contents);
    int written = fwrite(contents, 1, len, file);
    
    if (!(written == len)) {
        printf("Error writing to file");
        fclose(file);
        return (0-1);
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
    int length,
    int capacity,
}

struct string_vec {
    ptr string items,
    int length,
    int capacity,
}

func string str_init() {
    string made;
    made.data = malloc(0);
    made.data[0] = 0;
    made.length = 0;
    made.capacity = 0;
    return made;
}

func string str_from_cstr(ptr char cstr) {
    string made;
    made.length = strlen(cstr);
    made.data = malloc(made.length+1);
    memcpy(made.data, cstr, made.length+1);
    made.capacity = made.length;
    return made;
}

func void str_clear(ptr string __str, char c) {
    string _str = __str[0];
    _str.capacity = 0;
    _str.length = 0;
    _str.data[0] = 0;
    __str[0] = _str;
    return;
}

func void str_append(ptr string __str, char c) {
    string _str = __str[0];
    if (_str.capacity <= (_str.length+1)) {
        _str.capacity = _str.capacity*2;
        if (_str.capacity == 0) {
            _str.capacity = 1;
        };
        ptr char new_data = malloc(_str.capacity);
        memcpy(new_data, _str.data, _str.capacity);
        free(_str.data);
        _str.data = new_data;
    };
    _str.data[_str.length] = c;
    _str.length++;
    _str.data[_str.length] = 0;
    __str[0] = _str;
    return;
}

func void str_add(ptr string __str, ptr char cstr) {
    string _str = __str[0];
    int clen = strlen(cstr);
    if (_str.capacity <= (_str.length+clen)) {
        _str.capacity = (_str.capacity+clen)*2;
        if (_str.capacity == 0) {
            _str.capacity = clen;
        };
        ptr char new_data = malloc(_str.capacity);
        memcpy(new_data, _str.data, _str.capacity);
        free(_str.data);
        _str.data = new_data;
    };
    memcpy(cast _str.length+cast _str.data as int as ptr char, cstr, clen);
    _str.length = _str.length+clen;
    _str.data[_str.length] = 0;
    __str[0] = _str;
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
        if (_str.data == c) {
            0;
        };
    };
    return vtemp;
}

extern void va_start(ptr void)
extern void va_end(ptr void)
extern int vsnprintf(ptr void, ptr char, ptr char, ptr void)

ptr void NULL = 0

func ptr char str_fmt(ptr char fmt, <>) {
    ptr void args;
    va_start(&args);

    int size = vsnprintf(NULL, 0, fmt, args);
    va_end(args)
    
    if (size < 0) return NULL;
    
    ptr char buffer = malloc(size + 1);
    if (!buffer) return NULL;
    
    va_start(&args)

    vsnprintf(buffer, size + 1, fmt, args)
    va_end(args)

    return buffer;
}