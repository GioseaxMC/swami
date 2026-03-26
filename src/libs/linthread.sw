extern void pthread_create(ptr void, ptr void, ptr void, ptr void)
extern void pthread_join(int, ptr void)

func Thread makeThread(ptr void func_pointer, ptr void arg) {
    Thread thread;
    pthread_create(&thread.pthread, cast 0 as ptr void, func_pointer, arg);
    return thread;
}

func void waitThread(Thread t, ptr void res) {
    pthread_join(t.pthread, res);
}

func void closeThread(Thread t) {
    return void;
}

func void waitAndClose(Thread t, ptr void res) {
    waitThread(t, res);
    closeThread(t);
}

