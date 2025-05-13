extern ptr void realloc(ptr void, int)
extern ptr void malloc(int)
extern ptr void malloc(int)

extern void memcpy(ptr void, ptr void, int)

macro da_append(da, item) {
    if ((da).length >= ((da).capacity)) {
        (da).capacity = (da).capacity*2;
        if ((da).capacity == 0) {
            (da).capacity = 8;
        };
    };
    (da).items = realloc((da).items, (da).capacity*sizeof((da).items[0]));
    (da).items[(da).length] = (item);
    (da).length++;
}

macro da_init(da) {
    (da).items = malloc(0);
    (da).length = 0;
    (da).capacity = 0;
}

macro da_len(da) {
    ((da).length);
}

macro da_from_ptr(da, _ptr, _len) {
    (da).items = malloc(_len * sizeof(*_ptr));
    (da).length = _len;
    (da).capacity = _len;
    
    memcpy((da).items, _ptr, _len*sizeof(*_ptr));
}

macro da_begin(da) { (da).items; }

macro da_end(da) { cast cast (da).items as int + sizeof(*((da).items))*(da).length as ptr void; }

macro foreach(da, iter_t, iter_n, body) {
    for(
        ptr iter_t iter_n = da_begin(da),
        cast iter_n as int != cast da_end(da) as int,
        iter_n = cast cast iter_n as int + sizeof(*((da).items)) as ptr void,
            body
    );
}

macro dynamic_array(type, name) {
    struct name {
        ptr type items,
        int length,
        int capacity,
    };
}
