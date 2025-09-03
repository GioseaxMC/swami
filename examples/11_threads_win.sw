include { "stdlib.sw" }
include { "threads.sw" }

func void thread_func() {
    for (i=0, i<1000, i++, {
        printf("Sigma sigma boi %i\n", i);
    });
}

func void main() {
    t = makeThread(thread_func);

    if not t.handle {
        printf("Create thread failed\n");
        return;
    };

    for (i=0, i<1000, i++, {
        printf("Sigma outer boi\n");
    });

    waitAndClose(t);
}
