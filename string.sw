extern int strlen(ptr char)
extern void strcpy(ptr char, ptr char)
extern ptr void malloc(int)
extern void free(ptr void)
extern void exit(int)

struct string {
	ptr char data;
	int length;
	int capacity;
}

macro str_assert(cond, message) {
    if (!cond) { printf("ASSERT: %s", message); exit(0-1); }
}

func int next_powt(int len) {
    int temp = 1;
    while (temp <= len) {
        temp = temp * 2;
    }
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
    free(old_data);
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
        if(idx == _pos) {
            while (new_len > inserted) {
                str.data[idx+inserted] = _new[inserted];
                inserted++;
            }
        }
        str.data[idx+inserted] = old_data[idx];
        idx++;
    }
    str.length = str.length + new_len;
    str.data[str.length] = 0;
    free(old_data);
    _str[0] = str;
    return;
}

func void str_add(ptr string _str, ptr char _new) {
    string str = _str[0];
    str_insert(&str, str.length, _new);
    _str[0] = str;
    return;
}

func void str_remove(str string _str, int _pos, int _len) {
    string str = _str[0];
    str_assert(_len > 0, "length of remover must be more than 0");
    str_assert(_len+_pos <= (str.length), "removing out of range");
    int idx = 0;
    while (str.length-_pos-_len+1 > idx) {
        if (_pos+idx+_len <= length) {
            at(_pos+idx) = data[_pos+idx+_len];
        }
    }
    length -= _len;
    return self;

}

func void main() {
    string str = str_init();
    str_set(&str, "01234567");
    str_add(&str, "89");
    println(str.data);
    return;
}