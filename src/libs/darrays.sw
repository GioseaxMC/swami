extern ptr void realloc(ptr void, int)
extern ptr void malloc(int)

extern void memcpy(ptr void, ptr void, int)

macro _op_ptr(p1, s, p2) {
    cast cast p1 as int s cast p2 as int
    as ptr void;
}

macro da_reserve(da, new_size) {
    if (da).capacity < new_size {
        (da).capacity = new_size;
        (da).items = realloc((da).items,
            (da).capacity*sizeof(*((da).items)));
    };
}

macro da_append(da, item) {
    if (da).length >= ((da).capacity) {
        if (da).capacity 
            da_reserve(da, (da).capacity*2)
        else
            da_reserve(da, 16);
    };
    (da).items[(da).length] = (item);
    ++((da).length);
}

# this is now 'useless', keeping it for legacy code
    macro da_init(da) {
        (da).items = cast 0 as ptr void;
        (da).length = 0;
        (da).capacity = 0;
    }

    macro da_make(da_t, da) {{
        da_t da;
        da_init(da);
    };}
# end

macro da_len(da) {
    ((da).length);
}

macro da_from_ptr(da, _ptr, _len) {
    (da).items = malloc((_len) * sizeof(*_ptr));
    (da).length = (_len);
    (da).capacity = (_len);
    
    memcpy((da).items, _ptr, (_len)*sizeof(*_ptr));
    da;
}

macro da_begin(da) { (da).items; }

macro da_end(da) { &((da).items[(da).length]); }

macro da_last(da) { &((da).items[(da).length-1]); }

macro da_sizeof(da) { sizeof(*(da).items)*(da).length; }

macro foreach(da, _iter_n, body) {{
    _iter_n = da_begin(da);
    while( cast _iter_n as int != cast da_end(da) as int ) {
        body;
        _iter_n = cast cast _iter_n as int + sizeof(*((da).items)) as ptr void;
    };
};}

macro da_remove(da, idx) {{
    _iter_i = idx;
    while( _iter_i < (da).length ) {
        (da).items[_iter_i] = (da).items[_iter_i+1];
        _iter_i++;
    };
    (da).length--;
};}

macro da_remove_unordered(da, idx) {{
    (da).items[idx] = *da_end(da);
    (da).length--;
};}

macro da_free(da) {
    free((da).items);
    (da).items = NULL;
    (da).length = 0;
    (da).capacity = 0;
}

macro da_find_if(da, name, body) {
    foreach(da, name, {
        if (body) break;
    });
    name;
}

macro da_dist(da, _ptr) {
    cast _op_ptr(da_begin(da),-,_ptr) as int/sizeof(*da_begin(da));
}

macro dynamic_array(type, name) {
    struct name {
        int length,
        int capacity,
        ptr type items,
    };
}
