#include <stdio.h>

void hello(char* string) {
    printf("Hello, %s", string);
    return;
}

int main(int argc, char** argv) {
    hello("World!");
    return 0;
}