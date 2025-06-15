extern ptr void realloc(ptr void, int)
extern ptr void malloc(int)

extern void memcpy(ptr void, ptr void, int)

macro da_append(da, item) {
    if ((da).length >= ((da).capacity)) {
        (da).capacity = (da).capacity*2;
        if ((da).capacity == 0) {
            (da).capacity = 8;
        };
        (da).items = realloc((da).items, (da).capacity*sizeof(item));
    };
    (da).items[(da).length] = (item);
    ++((da).length);
}

macro da_init(da) {
    (da).items = cast 0 as ptr void;
    (da).length = 0;
    (da).capacity = 0;
}

macro da_make(da_t, da) {{
    da_t da;
    da_init(da);
};}

macro da_len(da) {
    ((da).length);
}

macro da_from_ptr(da, _ptr, _len) {
    (da).items = malloc((_len) * sizeof(*_ptr));
    (da).length = (_len);
    (da).capacity = (_len);
    
    memcpy((da).items, _ptr, (_len)*sizeof(*_ptr));
}

macro da_begin(da) { (da).items; }

macro da_end(da) { cast cast (da).items as int + sizeof(*((da).items))*(da).length as ptr void; }

macro foreach(da, _iter_t, _iter_n, body) {{
    ptr _iter_t _iter_n = da_begin(da);
    while( cast _iter_n as int != cast da_end(da) as int ) {
        body;
        _iter_n = cast cast _iter_n as int + sizeof(*((da).items)) as ptr void;
    };
};}

macro da_remove(da, idx) {{
    int _iter_i = 0;
    int _popped = 0;
    while( _iter_i < (da).length ) {
        if (_iter_i != idx) {
            (da).items[_iter_i - _popped] = (da).items[_iter_i];
        } else {
            _popped++;
        };
        _iter_i++;
    };
    (da).length = (da).length - _popped;
};}

macro da_free(da) {
    free((da).items);
    (da).items = NULL;
    (da).length = 0;
    (da).capacity = 0;
}

macro dynamic_array(type, name) {
    struct name {
        int length,
        int capacity,
        ptr type items,
    };
}
