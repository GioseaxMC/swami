include {
    "stdlib.sw",
    "darrays.sw",
    "pathlib.sw"
}

func int main() {
    Path path = path_init("/feels/good/to/eat/../be/king/ahah/");

    path_add(&path, "../.");

    foreach(path, p, {
        printf("%s/", *p);
    });
    
    printf("\n");
    path_free(&path);
    return 0;
}
