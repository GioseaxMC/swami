include { "stdlib.sw" }

func int main(int argc, ptr ptr char argv) {
    if argc < 2 {
        printf("Expected a name\n");
        return 1;
    };

    printf("Hello %s\n", argv[1]);
}
