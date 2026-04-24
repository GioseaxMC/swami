include {
    "stdlib.sw"
}

func void astruct_ptr_void_int_int_sum_int(ptr void _, int x) {
    println(x);
}

macro new_array(type) {
    { struct { ptr type items, int cap, int len }; };    
}

func int main()
{
    arr = new_array(void);
    
    println(&arr);

    arr+4;
}
