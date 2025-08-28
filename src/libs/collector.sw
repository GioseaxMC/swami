include { "stdlib.sw" }
include { "darrays.sw" }

struct MemChunk {
    ptr void memory,
    int size,
    int seen,
};

struct TapeCheckResults {
    int stack_count,
        int heap_count,
}

func MemChunk mc_malloc(int size) {
    MemChunk mc;
    mc.size = size;
    mc.memory = malloc(size);
    return mc;
}

dynamic_array(MemChunk, MemChunks);

MemChunks mcs;

struct GarbageCollector {
    ptr void stack_tail,
    int last_length,
    int threshold,
    ptr void (int) ptr alloc,
    ptr void (ptr void) ptr dealloc,
    void () ptr collect,
    void () ptr end,
}

GarbageCollector gc;

macro gc_init() {{
    int __started_gc__;
    if not gc.stack_tail {
        gc.stack_tail = &__started_gc__;
        gc.threshold = 2;
        gc.alloc = gc_alloc;
        gc.dealloc = gc_dealloc;
        gc.collect = gc_garbage_collect;
        gc.end = gc_end;
    };
    macro malloc(__alloca_size__) { gc.alloc(__alloca_size__); };
    macro realloc(original, size) {
        gc_realloc(original, size);
    };
    macro free  (__alloca_ptrr__) { gc .dealloc(__alloca_ptrr__); };
    &mcs;
};}

func ptr void gc_alloc(int size) {
    mc = mc_malloc(size);
    da_append(mcs, mc);
    if (mcs.length >= gc.last_length*gc.threshold) {
        gc.collect();
        gc.last_length = mcs.length;
    };
    return mc.memory;
}

func ptr void gc_realloc(ptr void og, int size) {
    ret = gc.alloc(size);
    memcpy(ret, og, size);
    gc.dealloc(og);
    ret;
}

func void gc_dealloc(ptr void pointer) {
    result = da_find_if(mcs, $, {
        op_ptr(pointer,==,$.memory);
    });

    if op_ptr(result,==,da_end(mcs)) {
        printf("Cannot dealloc %p as it was not allocated with gc.alloc()\n", pointer);
        exit(-1);
    };
    
    dist = da_dist(mcs, result);
    da_remove_unordered(mcs, dist);
    
    free(pointer);
}


func TapeCheckResults check_tape(ptr int start, ptr int tail) {
    TapeCheckResults tcr;
    
    for(
    ptr int rsp = start,
    op_ptr(rsp,<,tail),
    rsp = op_ptr(rsp,+,sizeof(int)), {
        found = da_find_if(mcs, $, op_ptr($.memory,==,*rsp));
        if found != da_end(mcs) {
            if !found.seen {
                tcr.stack_count++;
                res = check_tape(
                    found.memory,
                    op_ptr(found.memory,+,found.size)
                );
                tcr.heap_count =
                    tcr.heap_count+
                    res.stack_count+
                    res.heap_count;
                ++(found.seen);
            };
        };
    });

    tcr;
}

func void prepare_tape_check() {
    foreach(mcs, $, $.seen = 0);
}

func void gc_garbage_collect() {
    int freed;
    ptr void stack_start = &freed;

    prepare_tape_check();
    res = check_tape(stack_start, gc.stack_tail); #check stack and heap recursively

    printf("stack pointers: %i\nheap pointers: %i\n", res);

    for(i=0, i<mcs.length, i++, { # dealloc unreachables
        if !(mcs.items[i].seen) {
            freed++;
            free(mcs.items[i].memory);
            da_remove_unordered(mcs, i--);
        };
    });
    
    # return;

    if freed == 1
        printf("Freed 1 dangling pointer\n")
    else if freed
        printf("Freed %i dangling pointers\n", freed)
    else
        printf("No dangling pointers to be freed\n");
}

func void gc_end() {
    gc.collect();
    foreach(mcs, mc, {
        free(mc.memory);
    });
    da_free(mcs);
}

macro gc_defer(defer, body) {{
    body;
    defer;
};}

macro gc_collected(body) {
    gc_defer(gc.end(), body);
}

macro fun(funcstuff__, body__) {
    func funcstuff__ {
        gc_init();
        gc_collected(body__);
    };
}
