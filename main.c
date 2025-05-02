#include <stdio.h>

int main(void) {
    int x = 1;
    int y = x<<4;

    printf("Hello World %i\n", x, y);

    if (x && y) {
        printf("Hello World %i\n", x, y);
    }

    return 0;
}