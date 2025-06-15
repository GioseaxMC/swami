extern ptr void fopen(ptr void, ptr char)
extern ptr void fdopen(int, ptr char)
extern int rewind(ptr void)
extern int fseek(ptr void, int, int)
extern int ftell(ptr void)
extern int fclose(ptr void)
extern int fwrite(ptr char, int, int, ptr void)
extern int fread(ptr void, int, int, ptr void)

extern void write(int, ptr char, int)

extern int strlen(ptr char)

extern ptr void malloc(int)

ptr void FAILED_TO_READ = 0

int STDIN_FILENO = 0
int STDOUT_FILENO = 1
int STDERR_FILENO = 2

# ptr void stdout = fdopen(STDOUT_FILENO, "w")
# ptr void stdin = fdopen(STDIN_FILENO, "w")
# ptr void stderr = fdopen(STDERR_FILENO, "w")

int FAILED_TO_OPEN = -1
int FAILED_TO_WRITE = -2
int WRITE_SUCCESS = 0

func int write_file(ptr char filename, ptr char contents) {
    ptr void file = fopen(filename, "wb");
    if (!(file == cast 0 as ptr void)) {
        fclose(file); 
        return FAILED_TO_OPEN;
    };
    
    int len = strlen(contents);
    int written = fwrite(contents, 1, len, file);
    
    if (!(written == len)) {
        fclose(file);
        return FAILED_TO_WRITE;
    };
    fclose(file);
    return WRITE_SUCCESS;
}

func ptr char read_file(ptr char filename, ptr int size) {
    ptr void file = fopen(filename, "rb");
    if (!file) return cast 0 as ptr void;

    fseek(file, 0, 2);
    size[0] = ftell(file);
    rewind(file);

    ptr char buffer = malloc(size[0]+1);
    if !buffer { fclose(file); return cast 0 as ptr void; };

    fread(buffer, 1, size[0], file);
    buffer[size[0]] = 0;

    fclose(file);
    return buffer;
}
