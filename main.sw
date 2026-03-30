include {
    "stdlib.sw"
}

macro __fmt(type) {
    generic(type,
        bool: "%d",
        int: "%d",
        i16: "%hd",
        i32: "%ld",
        i64: "%lld",
        char: "%c",
        ptr char: "%s",
        ptr void: "%p",
        default: "%%?"
    );
}

macro __tern(cond, _t, _f) {
    cast (cond) as int *(_t) + cast (!cond) as int *(_f);
}

macro __print_one(x) {
    generic(x,
        bool: printf("%s", __tern(x, "true", "false")),
        default: printf(__fmt(x), x)
    );
}

macro __print_oneln(x) {
    __print_one(x);
    printf("\n");
}

func int main() {

    __print_oneln(67);
    __print_oneln(true);
    __print_oneln("Hello World!");
    __print_oneln(cast 45 as i16);
    __print_oneln(cast 45 as i32);
    __print_oneln(*"Giose");
    __print_oneln(SS("sigma"));

    return 0;
}