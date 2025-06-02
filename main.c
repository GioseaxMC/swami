#include <stdio.h>

typedef struct {
    int x;
} Com;

int main(void) {
    Com a;
    Com b = {0};
    return a == b;
}
