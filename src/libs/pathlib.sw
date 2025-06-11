# requires:
#   - stdlib.sw
#   - darrays.sw

struct Path {
    ptr ptr char items,
    int length,
    int capacity,
}

func void path_add(ptr Path path, ptr char _pathstr) {
    String pathstr = SS(_pathstr);
    String_vec elements = str_split(pathstr, *"/");
    foreach(elements, String, it, {
        if streq(it.items, ".") {
            str_free(*it);

        } else if streq(it.items, "..") {
            str_free(*it);
            if path.length {
                free(path.items[path.length-1]);
                da_remove(path, path.length-1);
            };

        } else if !streq(it.items, "") {
            da_append(path, it.items);

        } else {
            str_free(*it);
        };
    });
    da_free(elements);
    str_free(pathstr);
}

func Path path_init(ptr char _pathstr) {
    Path path;
    da_init(path);
    path_add(&path, _pathstr);
    return path;
}

func void path_free(ptr Path path) {
    foreach(path, ptr char, str, {
        free(*str);
    });
    da_free(path);
}

func void path_reset(ptr Path path) {
    foreach(path, ptr char, str, {
        free(str);
    });
    path.length = 0;
}

func String path_str(Path path) {
    String pathstr = SS("");
    pathstr;
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
