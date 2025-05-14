include { "stdlib.sw" }
include { "darrays.sw" }

extern int atoi(ptr char)
extern int strlen(ptr char)

dynamic_array(ptr char, ArgNames)
dynamic_array(ptr char, ArgDescs)
dynamic_array(ptr void, ArgPoint)
dynamic_array(int,      ArgTypes)

dynamic_array(ptr char, ParserArgs)

int StrArg = 0
int IntArg = 1
int BoolArg = 2

struct Parser {
    ArgNames names,
    ArgPoint pointers,
    ArgTypes types,
    ArgDescs descs,
}

func Parser make_parser() {
    Parser parser;
    da_init(parser.names);
    da_init(parser.pointers);
    da_init(parser.types);
    da_init(parser.descs);
    return parser;
}

func ptr void add_arg(ptr Parser _parser, ptr char arg_name, ptr char desc, int atype) {
    Parser parser = *_parser;
    ptr void pointer = malloc(8);
    

    da_append(parser.names, arg_name);
    da_append(parser.pointers, pointer);
    da_append(parser.types, atype);
    da_append(parser.descs, desc);
    
    if (atype == BoolArg) { *cast pointer as ptr int = 0; };

    *_parser = parser;
    return pointer;
}

func void parse_args(ptr Parser _parser, ptr ParserArgs argv) {
    int is_flag;
    int flag_pos;
    foreach(*argv, ptr char, arg, {
        is_flag  = 0;
        flag_pos = 0;
        foreach(*_parser.names, ptr char, name, {
            if (streq(*name, *arg)) {
                is_flag = 1;
            } else if (!is_flag) {
                flag_pos++;
            };
        });
        if (is_flag) {

            if (*_parser.types.items[flag_pos] == IntArg) {
                arg = cast cast arg as int + sizeof(ptr char) as ptr void;
                *cast (*_parser.pointers.items[flag_pos]) as ptr int = atoi(*arg);

            } else if (*_parser.types.items[flag_pos] == StrArg) {
                arg = cast cast arg as int + sizeof(ptr char) as ptr void;
                ptr char _str = malloc(sizeof(ptr char));
                memcpy(_str, *arg, strlen(*arg)+1);

                *cast (*_parser.pointers.items[flag_pos]) as ptr ptr char = _str;
            } else if (*_parser.types.items[flag_pos] == BoolArg) {
                *cast (*_parser.pointers.items[flag_pos]) as ptr int = 1;
            };
        };
        
    });

    return;
}



func int main(int argc, ptr ptr char _argv) {
    
    # initialize the parser
    Parser parser = make_parser();
    

    # add the flags
    ptr int n = add_arg(&parser, "-n", "Its a number", IntArg);
    *n = 0;

    ptr ptr char p = add_arg(&parser, "-p", "It's a word", StrArg);
    *p = "(null)";

    ptr ptr int debug = add_arg(&parser, "-d", "Do debugging", BoolArg);
    

    # prepare argv into a dynamic array
    ParserArgs argv;
    da_from_ptr(argv, _argv, argc);
    

    # parse the arguments
    parse_args(&parser, &argv);
    

    printf("N: %i\n", *n + 10);
    printf("P: %s\n", *p);
    printf("D: %i\n", *debug);
    
    return 0;
}
