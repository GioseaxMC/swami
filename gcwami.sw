include { "stdlib.sw" }
include { "darrays.sw" }

struct MemChunk {
    ptr void memory,
    int size,
    int seen,
};

func MemChunk mc_malloc(int size) {
    MemChunk mc;
    mc.size = size;
    mc.memory = malloc(size);
    return mc;
}

dynamic_array(MemChunk, MemChunks);

MemChunks mcs;

struct GcFunctions {
    ptr void stack_tail,
    ptr void (int) ptr alloc,
    ptr void (ptr void) ptr free,
}

GcFunctions gc;

macro gc_init() {{
    int __started_gc;
    gc.stack_tail = &__started_gc;
    gc.alloc = gc_alloc;
    gc.free = gc_free;
    &mcs;
};}

func ptr void gc_alloc(int size) {
    mc = mc_malloc(size);
    da_append(mcs, mc);
    return mc.memory;
}

func void gc_free(ptr void pointer) {
    result = da_find_if(mcs, $, {
        op_ptr(pointer,==,$.memory);
    });
    if op_ptr(result,==,da_end(mcs)) {
        printf("Cannot free %p as it was not allocated with gc.alloc()\n", pointer);
        exit(-1);
    };
    
    dist = da_dist(mcs, result);

    printf("At index: %i\n", dist);
    free(pointer);
}













