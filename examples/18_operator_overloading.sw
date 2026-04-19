include { "stdlib.sw" }

struct Ints {
    int count,
    int cap,
    ptr int items,
}

func void Ints_assign_int(ptr Ints ints, int cap) {
    ints.count = 0;
    ints.cap = cap;
    ints.items = malloc(cap*sizeof(int));
}

func ptr int Ints_index_int(Ints arr, int idx) {
    return &arr.items[idx];
}

func void Ints_smaller_eq_int(ptr Ints arr, int item) {
    (*arr)[arr.count++] = item;
}

func int main()
{
    Ints ints = 256;

    ints <= 67;
    ints <= 420;

    for(i=0, i<ints.count, i++, {
        println(*ints[i]);
    });
}
