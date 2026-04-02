include {
    "stdlib.sw",
    "darrays.sw",
}

extern int atoi(ptr char)
extern int strlen(ptr char)

# dynamic_array(ptr char, ArgNames)
# dynamic_array(ptr char, ArgDescs)
# dynamic_array(ptr void, ArgPoint)
# dynamic_array(int,      ArgTypes)

# dynamic_array(ptr char, PosArgs)

struct ParserArgs {
    int length,
    ptr ptr char items,
}

int StrArg = 0
int IntArg = 1
int BoolArg = 2

struct Parser {
    ptr ptr char names,
    ptr ptr void pointers,
    ptr int types,
    ptr ptr char descs,
    
    ptr ptr char positionals,
    ptr char desc,
}

func Parser make_parser(ptr char desc) {
    Parser parser;
    parser.desc = desc;
    return parser;
}

func ptr ptr char args_as_da(int argc, ptr ptr char argv) {
    ptr ptr char array;
    for(i=0, i<argc, ++i, {
        arr_push(array, argv[i]);
    });
    return array;
}

func ptr void add_arg_impl(ptr Parser parser, ptr char arg_name, ptr char desc, int atype) {
    ptr void pointer = malloc(8);
    
    arr_push(parser.names, arg_name);
    arr_push(parser.pointers, pointer);
    arr_push(parser.types, atype);
    arr_push(parser.descs, desc);
    
    if (atype == BoolArg) { *cast pointer as ptr int = 0; };

    return pointer;
}

macro add_integer_arg(__parser, __arg_name, __desc) {
    cast add_arg_impl(&__parser, __arg_name, __desc, IntArg) as ptr int;
}

macro add_option(__parser, __arg_name, __desc) {
    cast add_arg_impl(&__parser, __arg_name, __desc, BoolArg) as ptr int;
}

macro add_string_arg(__parser, __arg_name, __desc) {
    cast add_arg_impl(&__parser, __arg_name, __desc, StrArg) as ptr ptr char;
}

func void parser_show_help(ptr Parser parser, ptr ParserArgs argv) {
    int arg_idx = 0;
    printf("%s\n\nUsage: %s\n", parser.desc, argv.items[0]);

    printf("  Arguments:\n");
    int atype;
    foreach(parser.names, arg, {
        printf("sas    %s ", *arg);
        atype = parser.types[arg_idx];
        if (atype != BoolArg) {
        
            printf("    %s ", *arg);

            if (atype == StrArg) { printf("<string> : "); } else { printf("<number> : "); };

            printf("%s\n", parser.descs[arg_idx]);

        };
        arg_idx++;
    });
    
    printf("\n  Options:\n");
    arg_idx = 0;
    foreach(parser.names, arg, {
        atype = parser.types[arg_idx];
        if (atype == BoolArg) {
            printf("    %s : %s\n", *arg, parser.descs[arg_idx]);
        };
        arg_idx++;
    });

    return;
}

func void parse_args(ptr Parser _parser, ptr ParserArgs argv) {
    int is_flag;
    int flag_pos;
    
    argv_end = _op_ptr(argv.items,+,sizeof(*argv.items)*argv.length);
    for(arg=argv.items, _op_ptr(arg,!=,argv_end),arg=_op_ptr(arg,+,sizeof(*arg)), {
        is_flag  = 0;
        flag_pos = 0;
        
        same = streq(*arg, "main");

        if (streq(*arg, "-h") || streq(*arg, "--help")) { parser_show_help(_parser, argv); exit(0); };
        foreach(_parser.names, name, {
            if (streq(*name, *arg)) {
                is_flag = 1;
            } else if (!is_flag) {
                flag_pos++;
            };
        });
        if (is_flag) {

            if (_parser.types[flag_pos] == IntArg) {
                arg = cast cast arg as int + sizeof(ptr char) as ptr void;
                *cast (_parser.pointers[flag_pos]) as ptr int = atoi(*arg);

            } else if (_parser.types[flag_pos] == StrArg) {
                arg = cast cast arg as int + sizeof(ptr char) as ptr void;
                ptr char _str = malloc(sizeof(ptr char));
                memcpy(_str, *arg, strlen(*arg)+1);

                *cast (_parser.pointers[flag_pos]) as ptr ptr char = _str;
            } else if (_parser.types[flag_pos] == BoolArg) {
                *cast (_parser.pointers[flag_pos]) as ptr int = 1;
            };
        } else {
            arr_push(_parser.positionals, *arg);
        };
        
    });

    return;
}
