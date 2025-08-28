include { "stdlib.sw" }
include { "collector.sw" }

fun( void main(),{
    reserve 800 as __;
    ptr ptr void x = __;

    for(i=0, i<100, i++, {
        printf("Iteration: %i\n", i);
        x[i%50] = malloc(8);
    });
});
