include {
    "stdlib.sw",
    "darrays.sw",
}

struct Allocation {
    ptr void memory,
    int size,
    bool seen,
}

struct Memory {
    ptr ptr void stack_tail,
    ptr Allocation allocations,
    int threshold,
    int last_len,
}

struct TapeCheck {
    int heap_count,
    int stack_count
}

Memory memory;

macro mm_init() {{
    int __memory_tail_marker__;
    memory.stack_tail = &__memory_tail_marker__;
    memory.threshold = 2;
    memory.allocations = new_array(Allocation);
};}

func void mm_prepare_tape() {
    foreach(memory.allocations, allocation, {
        allocation.seen = 0;
    });
}

func ptr Allocation mm__get_allocation_from_ptr(ptr ptr void rsp) 
{
    foreach(memory.allocations, allocation, {
        if op_ptr(allocation.memory,==,*rsp) return allocation;
    });
    return NULL;
}

func TapeCheck mm_check_tape(ptr ptr void start, ptr ptr void end) {
    TapeCheck res;

    for(
        rsp = start,
        op_ptr(rsp,<,end),
        rsp = op_ptr(rsp,+,sizeof(rsp)),
    {
        found = mm__get_allocation_from_ptr(rsp);
        if found {
            if !found.seen {
                res.stack_count++;
                lcr = mm_check_tape(found.memory, op_ptr(found.memory,+,found.size));
                found.seen++;
                res.heap_count = res.heap_count+lcr.stack_count+lcr.heap_count;
            };
        };
    });

    res;
}

func void mm_garbage_collect() {
    int freed;
    ptr ptr void __memory_start_marker__ = &freed;

    mm_prepare_tape();
    res = mm_check_tape(__memory_start_marker__, memory.stack_tail);
    
    for(i=0,i<arr_len(memory.allocations),++i, {
        allocation = memory.allocations[i];
        if !allocation.seen {
            free(allocation.memory);
            arr_unordered_remove(memory.allocations, i--);
            freed++;
        };
    });
}

func ptr void mm_alloc(int size)
{
    Allocation all;
    all.size = size;
    all.memory = malloc(size);
    if !all.memory return NULL;

    arr_push(memory.allocations, all);
    if arr_len(memory.allocations) >= memory.last_len*memory.threshold {
        println("last: ", memory.last_len, " current: ", arr_len(memory.allocations));
        mm_garbage_collect();
        memory.last_len = arr_len(memory.allocations);
    };
    return all.memory;
}

func void mm_deinit()
{
    foreach(memory.allocations, all, {
        free(all.memory);
    });
    arr_free(memory.allocations);
}

construct {
    mm_init();
    at_exit(mm_deinit);
}
