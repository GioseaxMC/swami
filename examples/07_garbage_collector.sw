include { "stdlib.sw" }
include { "collector.sw" }

func int main() {
    gc_init();
    
    ptr int pint;

    pint = gc.alloc(sizeof(int));
    pint = gc.alloc(sizeof(int));
    pint = gc.alloc(sizeof(int));
    pint = gc.alloc(sizeof(int));
    pint = gc.alloc(sizeof(int));
    pint = gc.alloc(sizeof(int));

    gc.free(pint); # the other pointers?

    gc.end(); # they are seen here

    return 0;
};



