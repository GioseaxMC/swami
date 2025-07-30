include {
    "pathlib.sw",
    "stdlib.sw",
    "files.sw",
}

func int main() {
    entries = make_entries(get_cwd());

    while e = next_entry(entries) {
        name = "file";
        if entry_is_dir(e) name = "dir";

        printf("[%s] %s\n", name, entry_path(e));
        free_entry(e);
    };

    free_entries(entries);
}
