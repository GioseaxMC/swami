extern void printf(ptr char, <>)

func void hello(ptr char string) {
    printf("Hello %s", string);
    return;
}

func void main(int argc, ptr ptr char argv) {
    hello("World!");
    return;
}