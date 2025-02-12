#include <stdio.h>
#include <stdlib.h>

int main() {

    int x = 69;
    int* y = (&x);
    y += 0;
    x = y[0];
}