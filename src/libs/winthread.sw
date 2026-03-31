@linux panic "WINthread.sw is a windows specific module, use linthread.sw or threads.sw"

extern int CreateThread(ptr void, i32, void(ptr void) ptr, ptr void, i32, ptr void)
extern int WaitForSingleObject(int, i32)
extern void CloseHandle(int);

i32 INFINITY = 4294967295;

struct WinThreadContext {
    ptr void in,
    ptr void out,
    ptr void func_pointer,
}

func void __win_thread_func_runner(ptr WinThreadContext ctx) {
    ptr void (ptr void) ptr fn = ctx.func_pointer;
    ctx.out = fn(ctx.in);
}

func Thread makeThread(ptr void func_pointer, ptr void arg) {
    Thread t;
    ptr WinThreadContext ctx = alloca(WinThreadContext);
    t.windows_context = ctx;
    ctx.in = arg;
    ctx.func_pointer = func_pointer;

    t.handle = CreateThread(cast 0 as ptr void, 0, __win_thread_func_runner, ctx, 0, &t.id);
    return t;
}

func void waitThread(Thread t, ptr void res) {
    WaitForSingleObject(t.handle, INFINITY);
    ctx = cast t.windows_context as ptr WinThreadContext;
    ptr ptr void _res = res;
    if res {*_res = ctx.out;};
}

func void closeThread(Thread t) {
    CloseHandle(t.handle);
    free(t.windows_context);
}

func void waitAndClose(Thread __thread, ptr void res) {
    waitThread(__thread, res);
    closeThread(__thread);
}

