include {
    "stdlib.sw",
    "memory.sw",
    "darrays.sw",
}

struct Str {
    ptr char data,
    int len,
    int cap,
}

macro str(x) {
    generic(x,
        int: any_to_str(x),
        i16: any_to_str(x),
        i32: any_to_str(x),
        i64: any_to_str(x),
        char: any_to_str(x),
        bool: any_to_str(x),
        ptr void: any_to_str(x),
        ptr char: Str_when_ptr_char(Str, x),
        Str: (x),
        default: generic(Str->(x),
            Str: Str->(x),
            ptr char: Str_when_ptr_char(Str->(x))
        )
    );
}

func Str Str_call(Str self, ptr char data) { self = data; self; }

func Str str_join(Str self, ptr Str list) {
    assert(is_array(list), "str.join() can only take an array of list created with darrays.sw");
    Str new;
    if !arr_len(list) return new;
    new.cap = self.len*(arr_len(list)-1);
    foreach(list, item, new.cap=new.cap+item.len);
    new.data = mm_alloc(new.cap);

    foreach(list, item, {
        if op_ptr(item,!=,arr_start(list)) {
            memcpy(new.data+new.len, self.data, self.len);
            new.len = new.len + self.len;
        };
        memcpy(new.data+new.len, item.data, item.len);
        new.len = new.len + item.len;
    });
    
    assert(new.len == new.cap, "dbit natcg");

    new;
}

func void Str_assign_ptr_char(ptr Str self, ptr char other) {
    self.data = mm_alloc(strlen(other));
    memcpy(self.data, other, strlen(other));
    self.len = strlen(other);
    self.cap = self.len;
}

func bool Str_equal_Str(Str self, Str other) {
    if self.len != other.len return 0;
    for(i=0, i<self.len, i++, {
        if self.data[i] != other.data[i] return 0;
    });
    return 1;
}

func void Str_assign_Str(ptr Str new, Str other) {
    new.data = mm_alloc(other.len);
    new.cap = other.len;
    new.len = other.len;
    memcpy(new.data, other.data, other.len);
}

func Str Str_sum_Str(Str a, Str b) {
    Str c;
    c.cap = (c.len = a.len+b.len);
    c.data = mm_alloc(c.cap);
    memcpy(c.data, a.data, a.len);
    memcpy(op_ptr(c.data,+,a.len), b.data, b.len);
    return c;
}

func Str Str_mul_int(Str a, int n) {
    Str b;
    b.cap = (b.len = a.len*n);
    b.data = mm_alloc(b.len);
    for (i=0,i<n,i++, {
        memcpy(op_ptr(b.data,+,i*a.len), a.data, a.len);
    });
    return b;
}

func void Printer_when_Str(ptr void _, Str str) {
    printf("%.*s", str.len, str.data);
}

func Str str_empty() {
    Str new = "";
    new;
}

func Str str_cut(Str self, int start, int end) {
    assert(start >= 0 || start <= self.len, "cutting start out of string");
    assert(end >= 0 || end <= self.len, "cutting end out of string");
    assert(end >= start, "cutting negative region is not possible");
    if end == start {
        return str_empty();
    };
    Str new;
    new.data = mm_alloc(end-start);
    new.len = end-start;
    new.cap = new.len;
    memcpy(new.data, self.data+start, new.len);
    return new;
}

func int str_find(Str self, Str delim) {
    for(i=0,i<=self.len-delim.len,++i,{
        if !memcmp(&self.data[i], delim.data, delim.len) return i;
    });
    return self.len + delim.len;
}

func Str str_chop(ptr Str self, Str delim) {
    Str cut;

    i = str_find(*self, delim);
    if i<=self.len-delim.len {
        cut = str_cut(*self, 0, i);
        self.data = self.data+(i+delim.len);
        self.len = self.len-(i+delim.len);
        return cut;
    };

    cut = *self;
    *self = str_empty();
    return cut;
}

func ptr Str str_split(Str line, Str delim) {
    strings = new_array_with_gc(Str);
    while line.len {
        s = str_chop(&line, delim);
        arr_push(strings, s);
    };
    return strings;
}

func void Printer_when_ptr_Str(ptr void _, ptr Str strings) {
    len = arr_len(strings);
    print("[");
    for(i=0,i<len,i++, {
        if i print(", ");
        print(strings[i]);
    });
    print("]");
}

func ptr char str_as_cstr(Str self) {
    ptr char cstr = mm_alloc(self.len+1);
    memcpy(cstr, self.data, self.len);
    cstr[self.len]=0;
    return cstr;
}

func Str Str_when_ptr_Str(Str _, ptr Str strings) {
    assert(is_array(strings), "strings must be array type when formatting");
    len = arr_len(strings);
    return str("[")+str_join(str(", "), strings)+str("]");
}

func Str Str_when_ptr_char(Str _, ptr char cstr) {
    Str s = cstr;
    return s;
}

macro any_to_str(arg) {{
    unroll (x) (__scramble__) { unroll (y) (__scramble__) {
        reserve 4096 as x;
        snprintf(x, 4096, __fmt(arg), arg);
        Str y = x;
        y;
    };};
};}

