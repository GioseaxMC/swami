include {
    "stdlib.sw",
    "darrays.sw"
}

extern ptr char getcwd(ptr char, int)
extern int chdir(ptr char)

struct Path {
    ptr ptr char items,
    int length,
    int capacity,
}

func ptr char get_cwd() { # swami's getcwd
    reserve 4096 as temp;
    getcwd(temp, 4096);
    int len = strlen(temp);
    ptr char buf = malloc(len+1);
    memcpy(buf, temp, len+1);
    return buf;
}

func void path_add(ptr Path path, ptr char _pathstr) {
    pathstr = SS(_pathstr);
    str_replace(&pathstr, "\\", "/");
    StringVec elements = str_split(pathstr, *"/");
    foreach(elements, it, {
        if streq(it.items, ".") {
            str_free(it);

        } else if streq(it.items, "..") {
            str_free(it);
            if path.length {
                free(path.items[path.length-1]);
                da_remove(path, path.length-1);
            };

        } else if !streq(it.items, "") { 
            da_append(path, it.items);

        } else {
            if path.length == 0 {
                da_append(path, "/");
            };
            str_free(it);
        };
    });
    da_free(elements);
    str_free(&pathstr);
}

func Path path_init(ptr char _pathstr) {
    Path path;
    da_init(path);
    path_add(&path, _pathstr);
    return path;
}

func void path_free(ptr Path path) {
    foreach(path, str, {
        free(*str);
    });
    da_free(path);
}

func void path_reset(ptr Path path) {
    foreach(path, str, {
        free(str);
    });
    path.length = 0;
}

func String path_str(Path path) {
    String pathstr = SS("");
    foreach(path, item, {
        str_add(&pathstr, *item);
        if op_ptr(item, !=, da_end(path)) {
            str_add(&pathstr, "/");
        };
    });
    pathstr;
}

func Path get_cwd_as_path() {
    reserve 1024 as cwd;
    getcwd(cwd, 1024);
    Path pcwd = path_init(cwd);
    pcwd;
}

# func int main() {
# 
#     Path path = path_init("/feels/good/to/eat/../be/king/ahah/");
#     path_add(&path, "../.");
#     foreach(path, ptr char, p, {
#         printf("%s/", *p);
#     });
#     
#     printf("\n");
# 
#     path_free(&path);
# 
#     return 0;
# }
