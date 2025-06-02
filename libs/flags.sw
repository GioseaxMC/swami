include {
    "stdlib.sw",
    "darrays.sw",
}

extern int atoi(ptr char)
extern int strlen(ptr char)

dynamic_array(ptr char, ArgNames)
dynamic_array(ptr char, ArgDescs)
dynamic_array(ptr void, ArgPoint)
dynamic_array(int,      ArgTypes)

dynamic_array(ptr char, PosArgs)

dynamic_array(ptr char, ParserArgs)

int StrArg = 0
int IntArg = 1
int BoolArg = 2

struct Parser {
    ArgNames names,
    ArgPoint pointers,
    ArgTypes types,
    ArgDescs descs,
    
    PosArgs  positionals,
    ptr char desc,
}

func Parser make_parser(ptr char desc) {
    Parser parser;
    da_init(parser.names);
    da_init(parser.pointers);
    da_init(parser.types);
    da_init(parser.descs);
    da_init(parser.positionals);
    parser.desc = desc;
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

func void parser_show_help(ptr Parser parser, ptr ParserArgs argv) {
    int arg_idx = 0;
    printf("%s\n\nUsage: %s\n", *parser.desc, *argv.items[0]);

    printf("  Arguments:\n");
    int atype;
    foreach(*parser.names, ptr char, arg, {
        atype = *parser.types.items[arg_idx];
        if (atype != BoolArg) {
        
            printf("    %s ", *arg);

            if (atype == StrArg) { printf("<string> : "); } else { printf("<number> : "); };

            printf("%s\n", *parser.descs.items[arg_idx]);

        };
        arg_idx++;
    });
    
    printf("\n  Options:\n");
    arg_idx = 0;
    foreach(*parser.names, ptr char, arg, {
        atype = *parser.types.items[arg_idx];
        if (atype == BoolArg) {
            printf("    %s : %s\n", *arg, *parser.descs.items[arg_idx]);
        };
        arg_idx++;
    });

    return;
}

func void parse_args(ptr Parser _parser, ptr ParserArgs argv) {
    int is_flag;
    int flag_pos;
    foreach(*argv, ptr char, arg, {
        is_flag  = 0;
        flag_pos = 0;

        if (streq(*arg, "-h") || streq(*arg, "--help")) { parser_show_help(_parser, argv); exit(0); };
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
        } else {
            da_append(*_parser.positionals, *arg);
        };
        
    });

    return;
}
