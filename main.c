#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>

char *format_string(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);

    // Get the required buffer size
    int size = vsnprintf(NULL, 0, fmt, args);
    va_end(args);

    if (size < 0) return NULL;  // Formatting error

    // Allocate the required space (+1 for null terminator)
    char *buffer = malloc(size + 1);
    if (!buffer) return NULL;  // Allocation failure

    va_start(args, fmt);
    vsnprintf(buffer, size + 1, fmt, args);
    va_end(args);

    return buffer;  // Caller must free this
}

int main() {
    char *result = format_string("Hello, %s!", "world");
    if (result) {
        printf("%s\n", result);
        free(result);  // Free the allocated memory
    }
    return 0;
}
