include {
    "stdlib.sw"
}

macro new_array(type) {
    func void astruct_ptr_@type@_sum_int(ptr void _, int x) { println(x); };

    { struct { ptr type items, i32 cap, i32 len }; };    
}

func int main()
{
    arr = new_array(void);

    arr+4;
}
