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


int STDIN_FILENO = 0
int STDOUT_FILENO = 1
int STDERR_FILENO = 2

# ptr void stdout = fdopen(STDOUT_FILENO, "w")
# ptr void stdin = fdopen(STDIN_FILENO, "w")
# ptr void stderr = fdopen(STDERR_FILENO, "w")

int OPEN_SUCCESS = 0
int FAILED_TO_OPEN = -1

int READ_SUCCESS = 0
int FAILED_TO_READ = -2

int WRITE_SUCCESS = 0
int FAILED_TO_WRITE = -3

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

struct File {
    ptr char contents,
    ptr char filename,
    int size,
    int error,
}

func File read_file(ptr char filename) {
    File ftemp;
    ftemp.size = 0;
    ftemp.contents = cast 0 as ptr void;
    ftemp.error = 0;
    ftemp.filename = filename;

    int size = 0;
    ptr void file = fopen(filename, "rb");
    if !file {
        ftemp.error = FAILED_TO_OPEN;
        return ftemp;
    };

    fseek(file, 0, 2);
    size = ftell(file);
    rewind(file);

    buffer = malloc(size+1);
    if !buffer {
        fclose(file);
        ftemp.error = FAILED_TO_READ;
    };

    fread(buffer, 1, size, file);
    buffer[size] = 0;
    
    ftemp.contents = buffer;

    fclose(file);
    return ftemp;
}
