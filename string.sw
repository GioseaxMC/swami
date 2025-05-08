extern int strlen(ptr char)
extern void strcpy(ptr char, ptr char)
extern ptr char strstr(ptr char, ptr char)
extern ptr void malloc(int)
extern void free(ptr void)
extern void exit(int)
extern void printf(ptr char, <>)

ptr void str_null = 0

macro _load(ptr) { ptr[0]; }

macro addptr(p, offset) { cast offset + cast p as int as ptr void; }

func bool is_letter(char letter) {
    return (letter >= 65 && letter <= 90) || (letter >= 97 || letter <= 122);
}

struct string {
	ptr char data,
	int capacity,
	int length,
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

func void main() {
    string str = str_init();

    str_set(&str, "1111");

    str_add(&str, "89");

    str_insert(&str, 0, "[");

    str_replace(&str, "1", "Ciao, ");

    str_add(&str, "]");
    
    printf("%s\n", str.data);

    return;
}