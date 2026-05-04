

include {
    "stdlib.sw",
    "memory.sw",
    "darrays.sw"
}

struct Str {
    ptr char data,
    int len,
    int cap,
}

func Str str_join(Str self, ptr Str list) {
    assert(is_array(list), "str.join() can only take an array of list created with darrays.sw");
    foreach(list, l, println(">> ", *l));
    Str new;
    if !arr_len(list) return new;
    new.cap = self.len*(arr_len(list)-1);
    foreach(list, item, new.cap=new.cap+item.len);
    foreach(list, l, println("> > ", *l));
    new.data = mm_alloc(new.cap);

    foreach(list, item, {
        println("- ", *item);
        if op_ptr(item,!=,arr_start(list)) {
            memcpy(new.data+new.len, self.data, self.len);
            new.len = new.len + self.len;
        };
        memcpy(new.data+new.len, item.data, item.len);
        new.len = new.len + item.len;
        println(new);
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
    new.cap = (new.len = other.len);
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

func int main()
{
    Str a = "=";
    Str b = ".";

    println(a*5);

    strings = new_array(Str);
    
    arr_push(strings, a);
    arr_push(strings, a);
    arr_push(strings, a);
    
    foreach(strings, s, println("> ", *s));
    foreach(strings, s, println("> ", *s));

    c = str_join(b, strings);
    
    foreach(strings, s, println("> ", *s));

    println(c);

    arr_free(strings);
}
