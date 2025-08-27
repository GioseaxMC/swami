include ( "gcwami.sw" )
include { "stdlib.sw" }

dynamic_array(int, Ints);

func int main() {
    gc_init();
    
    ptr int pint = gc.alloc(sizeof(int)*4);

    pint[0] = 1;
    pint[1] = 2;
    pint[2] = 3;
    pint[3] = 4;
    
    Ints ints;

    da_from_ptr(ints, pint, 4);

    gc.free(pint);
    gc.free(cast 4 as ptr void);

    foreach(ints, i, {
        printf("pint[ %i ]\n", *i);
    });

    return 0;
}
