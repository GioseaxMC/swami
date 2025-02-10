typedef struct { int* items; int length; int capacity; } integers;
typedef struct { float* items; int length; int capacity; } floats;

int main(int argc, char** argv) {
    integers intarray;
    (intarray).items = malloc(0); (intarray).length = 0; (intarray).capacity = 0;
    printf("length: %i\n", intarray.length);
    printf("capaci: %i\n", intarray.capacity);
}
