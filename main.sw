include {
    "stdlib.sw"
}

func int main() {
    @windows printf("Using Windows\n");
    @linux   printf("Using Linux\n");
    @macos   printf("Using MacOs\n");
}
