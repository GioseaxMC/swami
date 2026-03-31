include {
    "stdlib.sw",
    "darrays.sw",
}

func int main() {

    ptr int array;

    arr_push(array, 67);
    arr_push(array, 420);
    arr_push(array, 69);
    arr_push(array, 34);
    arr_push(array, 33);
    
    x = 56;

    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);
    printf("%d\n", x++);

    foreach(array, num, {
        printf("number: %i\n", *num);
    });
    
    return 0;
}
