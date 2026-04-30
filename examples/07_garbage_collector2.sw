include { "stdlib.sw" }
include { "memory.sw" }

func void main() {
    reserve 800 as __;
    ptr ptr void x = __;

    for(i=0, i<100, i++, {
        printf("Iteration: %i\n", i);
        x[i%50] = mm_alloc(8);
    });
}
