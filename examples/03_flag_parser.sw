ptr char sigma = "string 0\n";
ptr char sigma_ = "string 1\n";
ptr char sigma__ = "stirng 2\n";

include {
    "flags.sw"
}

func int main(int argc, ptr ptr char argv) {


    ParserArgs args;
    args.length = argc;
    args.items = argv;
    

    parser = make_parser("Flags library test program");

    n = add_integer_arg(parser, "-n", "It's a number");
    *n = 0;

    s = add_string_arg(parser, "-s", "It's a string");
    *s = "(null)";
    
    d = add_option(parser, "-d", "Do debugging");
    *d = 0;

    parse_args(&parser, &args);

    printf("N: %i\n", *n);
    printf("S: %s\n", *s);
    printf("D: %d\n", *d);
}
