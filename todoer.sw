include {
    "files.sw",
    "stdlib.sw",
    "darrays.sw",
    "pathlib.sw",
}

func int main(int argc, ptr ptr char argv) {
    ptr char cwd;
    if argc>1 {
        cwd = argv[1];
    } else {
        cwd = get_cwd();
    };

    printf("%s\n", cwd);

    0;
}
