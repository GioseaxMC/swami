#include <stdio.h>

int iota_counter = 0;

int iota() {
    iota_counter = iota_counter + 1;
    return iota_counter;
}

int main() {
    iota();
    iota();
    iota();
    iota();
    iota();
    iota();
    int var = iota();
    printf("%i", var);
    return 0;
}