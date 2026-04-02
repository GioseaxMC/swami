include {
    "stdlib.sw"
}

func void bye() {
    printf("Bye world\n");
}

func int main() {
    at_exit(bye);

    printf("Hello World\n");
}
