include {
    "stdlib.sw",
    "darrays.sw"
}

func i64 abs64(i64 n) {
    if n<0 n=n*-1;
    n;
}

func i32 abs32(i32 n) {
    if n<0 n=n*-1;
    n;
}

func i32 fvn1a_hash32(ptr char data, int size) {
    i32 fvn_prime = 16777619;
    i32 offset_basis = 2166136261;
    
    i = 0;
    _hash = offset_basis;
    while i<size {
        _hash = _hash | cast data[i] as i32;
        _hash = _hash * fvn_prime;
        i++;
    };
    abs32(_hash);
}

func i64 fvn1a_hash64(ptr char data, int size) {
    i64 fvn_prime = 1099511628211;
    i64 offset_basis = 14695981039346656037;
    
    i = 0;
    _hash = offset_basis;
    while i<size {
        _hash = _hash | cast data[i] as i64;
        _hash = _hash * fvn_prime;
        i++;
    };
    abs64(_hash);
}

func int fvn1a_hashint(ptr char data, int size) {
    int ret;
    if sizeof(int)==8 {
        ret = cast fvn1a_hash64(data, size) as int;
    } else {
        ret = cast fvn1a_hash32(data, size) as int;
    };
    ret;
}

macro hash(x, len) { fvn1a_hashint(x, len); }

macro hash_cstr(x) {
    hash(x, strlen(x));
}

struct HT_element {
    ptr void item,
    ptr char key
}

int HT_SIZE = 2048;

func ptr void _new_ht() {
    a = new_array_with_size(ptr HT_element, HT_SIZE);
    arr_len(a) = arr_capacity(a);
    return a;
}
# basically casting to type** just so i can use the type information to dereference inside macros, evil
macro new_ht(type) {
    cast _new_ht() as ptr ptr type;
}

func HT_element make_ht_element(ptr char k, int size) {
    HT_element e; e.key = strdup(k); e.item = malloc(size); e;
}

func ptr void _ht_get(ptr ptr HT_element ht, ptr char key, int sizeof_item) {
    h = hash_cstr(key) % HT_SIZE;
    if is_array(ht[h]) {
        foreach(ht[h], element, {if streq(element.key, key) return element.item;});
    };
    e = make_ht_element(key, sizeof_item);
    arr_push(ht[h], e);
    return e.item;
}

func ptr void _ht_find(ptr ptr HT_element ht, ptr char key) {
    h = hash_cstr(key) % HT_SIZE;
    if is_array(ht[h]) {
        foreach(ht[h], element, {if streq(element.key, key) return element.item;});
    };
    return NULL;
}

func ptr void _ht_pop(ptr ptr HT_element ht, ptr char key) {
    h = hash_cstr(key) % HT_SIZE;
    if is_array(ht[h]) {
        idx=0;
        while idx<arr_len(ht[h]) {
            if streq(ht[h][idx].key, key) {
                arr_unordered_remove(ht[h], idx);
                free(ht[h][idx].item);
                return ht[h][idx].item; # returning just to check if we freed the right pointer, must not be read into
            };
        };
    };
    return NULL;
}

macro ht_get(ht, key) {
    cast _ht_get(ht, key, sizeof(**ht)) as typeof(*ht);
}

macro ht_pop(ht, key) {
    cast _ht_pop(ht, key) as typeof(*ht);
}

macro ht_find(ht, key) {
    cast _ht_find(ht, key) as typeof(*ht);
}

func void ht_free(ptr ptr HT_element ht) {
    foreach(ht, array, {
        if is_array(*array) {
            foreach(*array, e, if e.item {
                free(e.item);
                free(e.key);
            });
            arr_free(*array); 
        };
    });
    arr_free(ht);
}

macro __get_key(e) {{ (e).key; };}
macro __get_item(e) {{ (e).item; };}

macro ht_foreach(ht, k_n, i_n, body) {{
    foreach(cast (ht) as ptr ptr HT_element, __ht_layer_1@k_n, {
        if is_array(*__ht_layer_1@k_n) {
            foreach(*__ht_layer_1@k_n, k_n@_e, {
                unroll (i_n) (cast __get_item(k_n@_e) as typeof(*ht)) {
                   unroll (k_n) (__get_key(k_n@_e)) { body; };
                };
            });
        };
    });
};}
