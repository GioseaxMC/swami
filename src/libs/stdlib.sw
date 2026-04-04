extern ptr void malloc(int)

macro alloca(type) { cast malloc(sizeof(type)) as ptr type; }

extern ptr void realloc(ptr void, int)

extern void free(ptr void)
extern void exit(int)
extern ptr char memset(ptr char, int, int)

extern int strlen(ptr char)
extern void strcpy(ptr char, ptr char)
extern ptr char strdup(ptr char)
extern ptr char strstr(ptr char, ptr char)
extern int strcmp(ptr char, ptr char)
extern int strncmp(ptr char, ptr char, int)

func int pow(int base, int power) {
    if !power return 0;

    int ini_base = base;

    int i=1; while i<power {
        base = ini_base * ini_base;
        ++i;
    };

    return base;
}

func bool isspace(char c) { return (c==9 || c==10 || c==11 || c==12 || c==13 || c==32); }

func bool isalnum(char c) {
    return (
        97 <= c && c <= 122 ||
        65 <= c && c <= 90  ||
        48 <= c && c <= 57
    );
}

macro streq(sstr, ssstr) { strcmp(sstr, ssstr) == 0; }


extern int vsnprintf(ptr void, ptr char, ptr char, ptr void)
extern int snprintf(ptr void, ptr char, ptr char, <>)
extern int printf(ptr char, <>)
extern int fprintf(ptr void, ptr char, <>)

extern void write(int, ptr char, int)
extern int read(int, ptr char, int)

@windows extern int Sleep(int)
@windows macro sleep(time) { Sleep(time); }
@linux extern int usleep(int)
@linux macro sleep(time) { usleep(time*1000); }

macro for(decl, cond, inc, body) {{
    decl;
    while (cond) { body; inc; };
};}

macro lambda_len(__arr__var, __criteria__func) {
    macro __arr__var@loop ( $ ) {
        { __arr__var@__i_counter_array=0; };
        while (__criteria__func) ++__arr__var@__i_counter_array;
        __arr__var@__i_counter_array;
    };
    __arr__var@loop(__arr__var[__arr__var@__i_counter_array]);
}

macro array_len(__arr__var) {
    lambda_len(__arr__var, $);
}

macro TODO(__random_shit) {
    panic "Not implemented yet."
}

ptr void nullptr = 0
ptr void NULL = 0
bool true = 1
bool false = 0

extern ptr void memcpy(ptr void, ptr void, int)

func int max(int a, int b) {
    if a > b return a;
    return b;
}

func int min(int a, int b) {
    if a < b return a;
    return b;
}

macro _load(ptr) { ptr[0]; }

macro op_ptr(p1, op, p2) { cast cast p1 as int op cast p2 as int as ptr void; }

macro addptr(__p__, __offset__) { op_ptr(__p__, +, __offset__); }

func int next_powt(int len) {
    int temp = 1;
    while (temp <= len) {
        temp = temp * 2;
    };
    return temp;
}


macro cstr_fmt(__fmt__, __args__) {{
    int __size__ = snprintf(NULL, 0, __fmt__, __args__);
    ptr char __str__ = malloc(__size__+1);
    snprintf(__str__, __size__+1, __fmt__, __args__);
    __str__;
};}

func void __write_and_free(int fp, ptr char str) { write(fp, str, strlen(str)); free(str); }

macro eprintf(__str__, __fmt__) {
    __write_and_free(2, cstr_fmt (__str__, __fmt__) );
}

# function that tells if a number is prime with 99.99% accuracy
func bool is_prime(int number) { return 0; }

extern int atexit(ptr void)

include { "darrays.sw" } # dont like this but at the same time the library is just macros

ptr ptr void __at_exit_funcs;

func void at_exit(ptr void fn) {
    arr_push(__at_exit_funcs, fn);
}

func void __do_at_exit() {
    if !__at_exit_funcs return;
    foreach(__at_exit_funcs, fn, {
        cast *fn as void()ptr ();
    });
}


ptr char _int_fmt;
construct {
    if sizeof(int)==8 _int_fmt="%lld" else _int_fmt="%d";
    atexit(__do_at_exit);
}

macro __fmt(type) {
    generic(type,
        int: _int_fmt,
        i16: "%hd",
        i32: "%d",
        i64: "%lld",
        char: "%c",
        bool: "%d",
        ptr char: "%s",
        default: "%%?"
    );
}

include { "sv.sw" }

macro __print_once(x) {
    generic(x,
        bool: if x printf("true") else printf("false"),
        StringView: sv_print(x),
        default: printf(__fmt(x), x)
    );
}

macro print(__args) {{
    unroll (_print_unroller) (__args) {
        __print_once(_print_unroller);
    };
};}

macro println(__args) {{
    print(__args);
    printf("\n");
};}

int __iota_counter = 0;
func int __iota__() { return __iota_counter++; }
func int __iota_reset__() { __iota_counter=0; return 0; }
macro enum(args) {
    unroll (arg) (args) {
        int arg;
    };
    construct {
        __iota_reset__();
        unroll(arg) (args) {
            arg = __iota__();
        };
    };
}

