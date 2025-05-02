extern void printf(ptr char, <>)

func int main() {

    ptr char x = "ciao";

    x[0] = -x[0];

    printf("%c", -x[0]);

    return 0;
}