include {
    "stdlib.sw",
    "flags.sw"
}

func int main(ParserArgs args) {
    parser = make_parser("OS teller");

    *(bits = add_integer_arg(parser, "-bits", "Bits of the machine")) =
        8*sizeof(ptr void);

    *(platform = add_string_arg(parser, "-plat", "The platform")) = (
        @windows "Windows",
        @linux "Linux",
    );

    parse_args(&parser, &args);

    printf("You're using %i bit %s\n", *bits, *platform);
    return 0;
}
