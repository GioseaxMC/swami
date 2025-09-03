struct Thread {
    i32 id,
    int handle,
    i64 padding,
}

@linux include { "linthread.sw" }

# windows

@windows include { "winthread.sw" }

@windows func Thread makeThread(ptr void func_pointer) {
    Thread t;
    t.handle = CreateThread(cast 0 as ptr void, 0, func_pointer, cast 0 as ptr void, 0, &t.id);
    return t;
}

@windows func void waitThread(Thread t) {
    WaitForSingleObject(t.handle, INFINITY);
}

@windows func void closeThread(Thread t) {
    CloseHandle(t.handle);
}

@windows func void waitAndClose(Thread __thread) {
    waitThread(__thread);
    closeThread(__thread);
}

