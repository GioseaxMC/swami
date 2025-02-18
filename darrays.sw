extern ptr void realloc(ptr void, int)
extern ptr void malloc(int)
extern ptr void malloc(int)

macro da_append(da, item) {
    if ((da).length >= ((da).capacity)) {
        (da).capacity = (da).capacity*2;
        if ((da).capacity == 0) {
            (da).capacity = 8;
        }
    }
    (da).items = realloc((da).items, (da).capacity*sizeofi((da).items[0]));
    (da).items[(da).length] = (item);
    (da).length++;
}

macro da_init(da) {
    (da).items = malloc(0);
    (da).length = 0;
    (da).capacity = 0;
}

macro da_len(da) {
    ((da).length)
}

macro dynamic_array(type, name) {
    struct name {
        ptr type items;
        int length;
        int capacity;
    }
}