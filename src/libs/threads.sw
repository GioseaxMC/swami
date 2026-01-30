struct Thread {
    i32 id,
    int handle,
    i64 padding,
    int pthread
}

@linux include { "linthread.sw" }

@linux func Thread _makeThread(ptr void func_pointer, ptr void arg) {
    Thread thread;
    pthread_create(&thread.pthread, cast 0 as ptr void, func_pointer, arg);
    return thread;
}

@linux func void _waitThread(Thread t, ptr void res) {
    pthread_join(t.pthread, res);
}

@linux func void _closeThread(Thread t) {
    return void;
}

@linux func void _waitAndClose(Thread t, ptr void res) {
    _waitThread(t, res);
    _closeThread(t);
}
# windows

@windows include { "winthread.sw" }

@windows func Thread makeThread(ptr void func_pointer, ptr void arg) {
    Thread t;
    t.handle = CreateThread(cast 0 as ptr void, 0, func_pointer, arg, 0, &t.id);
    return t;
}

@windows func void waitThread(Thread t, ptr void res) {
    WaitForSingleObject(t.handle, INFINITY);
}

@windows func void closeThread(Thread t) {
    CloseHandle(t.handle);
}

@windows func void waitAndClose(Thread __thread, ptr void res) {
    waitThread(__thread, res);
    closeThread(__thread);
}

