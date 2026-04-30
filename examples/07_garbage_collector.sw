include { "stdlib.sw" }
include { "memory.sw" }

func int main() {
    ptr int pint;

    pint = mm_alloc(sizeof(int));
    pint = mm_alloc(sizeof(int));
    pint = mm_alloc(sizeof(int));
    pint = mm_alloc(sizeof(int));
    pint = mm_alloc(sizeof(int));
    pint = mm_alloc(sizeof(int));

    return 0;
};
