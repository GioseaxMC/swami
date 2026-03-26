struct Thread {
    i32 id,
    int handle,
    i64 padding,
    int pthread,
    #windows stuff
    ptr void windows_context
}

@linux include { "linthread.sw" }
@windows include { "winthread.sw" }
