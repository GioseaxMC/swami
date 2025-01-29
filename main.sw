include "stdlib.sw";

extern ptr void fopen(ptr void, ptr char)
extern int fseek(ptr void, int, int)
extern int ftell(ptr void)
extern int rewind(ptr void)
extern int fclose(ptr void)
extern int fread(ptr void, int, int, ptr void)

func ptr char read_file(ptr char filename, ptr int _size) {
    ptr void file = fopen(filename, "rb");
    if (!file) return cast(ptr char, 0);

    fseek(file, 0, 2);
    _size[0] = ftell(file);
    rewind(file)

    ptr char buffer = cast(ptr char, malloc(_size[0]+1));
    if !buffer { fclose(file), return cast(ptr char, 0); }

    fread(buffer, 1, _size[0], file)
    buffer[_size[0]] = cast(char, 0);

    fclose(file);
    return buffer;
}

func void main() {
    int size;
    ptr char content = read_file("main.sw", &size);
    if content {
        printf("content: %s", content);
    }
    return;
}



