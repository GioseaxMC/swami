include {
    "stdlib.sw",
    "surl.sw",
    "darrays.sw",
}

dynamic_array(ptr char, Args)

func int main(int argc, ptr ptr char argv) {
    da_make(Args, args);

    da_from_ptr(args, cast addptr(argv, 8) as ptr ptr char, argc-1);
    
    surl_init({
        printf("Couldn't initialize surl\n");
        return 1;
    });
    
    foreach(args, arg, {
        surl_fetch(*arg, ptr char buffer, {
            printf("Couldn't fetch url");
            return -1;
        });
        printf("%s", buffer);
    });

    surl_close();
    da_free(args);

    return 0;
}

