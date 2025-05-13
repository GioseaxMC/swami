include { "stdlib.sw" }
include { "darrays.sw" }

dynamic_array(ptr char, ArgNames)
dynamic_array(ptr char, ArgDescs)
dynamic_array(ptr void, ArgPoint)
dynamic_array(int,      ArgTypes)

dynamic_array(ptr char, Args)

int IntArg = 0
int StrArg = 1

struct Parser {
    ArgNames names,
    ArgPoint pointers,
    ArgTypes types,
    ArgDescs descs,
}

func ptr void add_arg(ptr Parser _parser, ptr char arg_name, ptr char desc, int atype) {
    Parser parser = *_parser;

    ptr void pointer = malloc(8);

    da_append(parser.names, arg_name);
    da_append(parser.pointers, pointer);
    da_append(parser.types, atype);
    da_append(parser.descs, desc);

    *_parser = parser;
    return pointer;
}

func void parse_args(ptr Parser _parser, ptr Args argv) {
    int res;
    foreach(*argv, ptr char, arg, {
        printf("arg: |%s|\n", *arg);
    });

    return;
}

func int main(int argc, ptr ptr char _argv) {
    Args argv;
    da_from_ptr(argv, _argv, argc);

    Parser parser;
    parse_args(&parser, &argv);
    return 0;
}
