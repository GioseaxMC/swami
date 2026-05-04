extern ptr void realloc(ptr void, int)
extern ptr void malloc(int)

extern void memcpy(ptr void, ptr void, int)

macro _op_ptr(p1, s, p2) {
    cast cast p1 as Wint s cast p2 as Wint
    as ptr void;
}

struct Array_header {
    i64 probe,
    int len,
    int capacity,
    ptr void (ptr void, int) ptr realloc,
    ptr void (int) ptr alloc,
}

struct __caster {
    Array_header ah,
    ptr void data
} 

i64 ARR_SENTINEL = 59774906347
int ARRAY_INIT_CAPACITY = 256

macro array_data(arr) { cast _op_ptr(arr,+,sizeof(Array_header)) as ptr void; }
macro arr_header(arr) { cast _op_ptr(arr,-,sizeof(Array_header)) as ptr Array_header; }

func ptr void allocate_inited_array(int sizeof_item, int init_capacity, ptr void (int) ptr allocator) {
    size = sizeof_item * init_capacity + sizeof(Array_header);
    ptr Array_header array = allocator(size);
    memset(array, 0, size);
    array.capacity = init_capacity;
    array.probe = ARR_SENTINEL;
    return array_data(array);
}

macro new_array_with_size(type, size) { cast allocate_inited_array(sizeof(type), size, malloc) as ptr type; }

macro new_array(type) { new_array_with_size(type, ARRAY_INIT_CAPACITY); }

func ptr void _new_array_with_allocators(int type_size, ptr void all, ptr void rea) {
    new_arr = allocate_inited_array(type_size, ARRAY_INIT_CAPACITY, all);
    arr_header(new_arr).alloc = all;
    arr_header(new_arr).realloc = rea;
    new_arr;
}

macro new_array_with_allocators(type, all, rea) { cast _new_array_with_allocators(sizeof(type), all, rea) as ptr type; }

macro new_array_with_gc(type) { assert(__included__("memory.sw"), "memory.sw is required to use a gc'ed array"); new_array_with_allocators(type, mm_alloc, mm_realloc); }

func bool is_array(ptr void arr) { if !arr return 0; return arr_header(arr).probe == ARR_SENTINEL; }
macro arr_len(arr) {{ arr_header(arr).len; };}
macro arr_capacity(arr) {{ arr_header(arr).capacity; };}
macro arr_start(arr) {{ arr; };}
macro arr_end(arr) { _op_ptr((arr),+,arr_len(arr)*sizeof(*(arr))); }
macro arr_ensure(arr, new_size) {
    (arr) = array_data(arr_realloc(arr)(arr_header(arr), new_size));
    arr_capacity(arr) = new_size;
}
macro arr_push(arr, item) {
    if (!(arr)) { (arr) = allocate_inited_array(sizeof(*arr), ARRAY_INIT_CAPACITY, malloc); };
    (arr)[arr_len(arr)++] = (item);
    if (arr_len(arr) >= arr_capacity(arr)) arr_ensure((arr), arr_capacity(arr)*2);
}
macro arr_unordered_remove(arr, index) { (arr)[index] = (arr)[--arr_len(arr)]; }
macro arr_free(arr) { if is_array(arr) free(arr_header((arr))); }
macro arr_exists(arr, idx) { idx<arr_len(arr); }
macro foreach(da, _iter_n, body) {{
    _iter_n = arr_start(da);
    while _op_ptr(_iter_n,!=,arr_end(da)) {
        body;
        _iter_n = _op_ptr(_iter_n,+,sizeof(*(da)));
    };
};}
func ptr void _arr_copy(ptr void dest, ptr void arr, int item_size) {
    h = arr_header(arr);
    memcpy(dest, arr, arr_capacity(arr)*item_size+sizeof(Array_header));
    array_data(dest);
}
macro arr_copy(dest, arr) {
    cast _arr_copy(dest, arr, sizeof(*arr)) as typeof(arr);
}
func ptr void _arr_alloc(ptr void arr) {
    if arr_header(arr).alloc
        return arr_header(arr).alloc
    else
        return malloc;
}
macro arr_alloc(arr) { cast _arr_alloc(arr) as ptr void (int) ptr; }
func ptr void _arr_realloc(ptr void arr) {
    if arr_header(arr).realloc
        return arr_header(arr).realloc 
    else 
        return realloc; 
}
macro arr_realloc(arr) { cast _arr_realloc(arr) as ptr void (ptr void, int) ptr; }
