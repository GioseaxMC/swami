include {
    "flags.sw"
}

func void main(int argc, ptr ptr char argv) {
    args = args_as_da(argc, argv);

    foreach(args, arg, {
        printf("|%s|\n", *arg);
    });
}
