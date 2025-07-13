include {
    "stdlib.sw",
    "files.sw",
    "etonizer.sw"
}

func void main() {
    f = read_file("main.sw");
    
    if f.error {
        printf("Failed to open file, code: %i\n", f.error);
        return;
    };

    tokens = tokenize(f.contents, f.filename);
    
    while (more(tokens)) {
        printf("|%s|\n", consume(tokens).token);
    };
}







