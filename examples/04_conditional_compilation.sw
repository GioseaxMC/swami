include {
    "stdlib.sw"
}

func int main(int argc, ptr ptr char argv) {
    @windows printf("Using Windows\n");
    @linux   printf("Using Linux\n");
    @macos   printf("Using MacOs\n");
}
