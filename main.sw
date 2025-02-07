include "stdlib.sw";
include "darrays.sw";

dynamic_array(int, int_array)

func void main() {
    int_array vec;
    da_init(vec);
    da_append(vec, 100);
    da_append(vec, 69);
    da_append(vec, 420);
    da_append(vec, 8);

    int i = 0;
    while (vec.length > i) {
        printf("item: %i at index %i\n", vec.items[i], i)
        i++;
    }

    return;
}