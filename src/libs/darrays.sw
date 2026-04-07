extern ptr void realloc(ptr void, int)
extern ptr void malloc(int)

extern void memcpy(ptr void, ptr void, int)

macro _op_ptr(p1, s, p2) {
    cast cast p1 as int s cast p2 as int
    as ptr void;
}

struct Array_header {
    int len,
    int capacity,
    i64 probe,
}

struct __caster {
    Array_header ah,
    ptr void data
} 

i64 ARR_SENTINEL = 59774906347
int ARRAY_INIT_CAPACITY = 256

macro array_data(arr) { cast _op_ptr(arr,+,sizeof(Array_header)) as ptr void; }
macro arr_header(arr) { cast _op_ptr(arr,-,sizeof(Array_header)) as ptr Array_header; }

func ptr void allocate_inited_array(int sizeof_item, int init_capacity) {
    size = sizeof_item * init_capacity + sizeof(Array_header);
    ptr Array_header array = malloc(size);
    memset(array, 0, size);
    array.capacity = init_capacity;
    array.probe = ARR_SENTINEL;
    return array_data(array);
}

macro new_array_with_size(type, size) { cast allocate_inited_array(sizeof(type), size) as ptr type; }
macro new_array(type) { new_array_with_size(type, ARRAY_INIT_CAPACITY); }
func bool is_array(ptr void arr) { if !arr return 0; return arr_header(arr).probe == ARR_SENTINEL; }
macro arr_len(arr) {{ arr_header(arr).len; };}
macro arr_capacity(arr) {{ arr_header(arr).capacity; };}
macro arr_start(arr) {{ arr; };}
macro arr_end(arr) { _op_ptr((arr),+,arr_len(arr)*sizeof(*(arr))); }
macro arr_ensure(arr, new_size) {
    (arr) = array_data(realloc(arr_header(arr), arr_capacity(arr)*2));
    arr_capacity(arr) = new_size;
}
macro arr_push(arr, item) {
    if (!(arr)) { (arr) = allocate_inited_array(sizeof(*arr), ARRAY_INIT_CAPACITY); };
    (arr)[arr_len(arr)++] = (item);
    if (arr_len(arr) >= arr_capacity(arr)) arr_ensure((arr), arr_capacity(arr)*2);
}
macro arr_unordered_remove(arr, index) { (arr)[index] = (arr)[--arr_len(arr)]; }
macro arr_free(arr) { free(arr_header((arr))); }
macro arr_exists(arr, idx) { idx<arr_len(arr); }
macro foreach(da, _iter_n, body) {{
    _iter_n = arr_start(da);
    while _op_ptr(_iter_n,!=,arr_end(da)) {
        body;
        _iter_n = _op_ptr(_iter_n,+,sizeof(*(da)));
    };
};}

