include { "stdlib.sw" }

func int main() {
    str_make(str, "Hello Better World!\n");
    printf( c(str) );

    return 0;
}