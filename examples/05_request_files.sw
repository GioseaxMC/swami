include {
    "flags.sw",
    "surl.sw",
}

func int main(int argc, ptr ptr char argv) {
    args = args_as_da(argc, argv);

    surl_init({
        printf("Couldn't initialize surl\n");
        return 1;
    });
    
    buffer = "";

    foreach(args, arg, {
        if arg != args.items surl_fetch(*arg, buffer, {
                printf("Couldn't fetch url");
                return -1;
        });
        printf("%s", buffer);
    });

    surl_close();
    da_free(args);

    return 0;
}

