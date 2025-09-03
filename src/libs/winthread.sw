@linux panic "WINthread.sw is a windows specific module, use linthread.sw (not yet) or threads.sw"

extern int CreateThread(ptr void, i32, void(ptr void) ptr, ptr void, i32, ptr void)
extern void WaitForSingleObject(int, i32)
extern void CloseHandle(int);

int INFINITY = 4294967296;
