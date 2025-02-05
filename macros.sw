extern ptr void realloc(ptr void, int, int)

int __da_init_cap = 8;

macro da_append(da, item) {
    if ((da).length >= (da).capacity) {
        (da).capacity = (da).capacity*2;
        if ((da).capacity == 0) {
            (da).capacity = __da_init_cap;
        }
        (da).items = realloc((da).items, (da).capacity*sizeof((da).items[0]));
    }
    (da).length++
    (da).items[(da).length] = (item);
}