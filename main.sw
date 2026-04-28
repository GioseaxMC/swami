include {
    "stdlib.sw",
    "memory.sw"
}

func void main()
{
    println("Hello World");
    
    ptr ptr ptr void p = mm_alloc(sizeof(ptr void));
    *p = mm_alloc(sizeof(ptr void)); # will shadow
    **p = mm_alloc(sizeof(ptr void)); # will shadow
    **p = mm_alloc(sizeof(ptr void)); # will shadow
    **p = mm_alloc(sizeof(ptr void)); # will shadow
    **p = mm_alloc(sizeof(ptr void)); # will shadow
    *p = mm_alloc(sizeof(ptr void));
}
