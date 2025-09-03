include { 
    "stdlib.sw", 
    "threads.sw",
    "stores.sw"
}

store_of(int);

intStore number;

func void proc() {
    st_subscribe(number, i, {
        if i++
            printf("Proc is late\n")
        else
            printf("Proc is the first\n");
        sleep(1000);
    });
}

func void main() {
    t = makeThread(proc);
    
    sleep(1);
    st_subscribe(number, i, {
        if i++
            printf("Main is late\n")
        else
            printf("Main is the first\n");
    });

    waitAndClose(t);
}
