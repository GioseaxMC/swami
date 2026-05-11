include {
    "stdlib.sw",
    "darrays.sw",
    "strings.sw",
}

struct Path {
    ptr Str items,
}

@windows OS_PATH_DELIMITER = "\\";
@linux OS_PATH_DELIMITER = "/";
PATH_DELIMITER = "/";

func Path Path_div_Path(Path self, Path other) {
    if !is_array(self.items) self.items = new_array_with_gc(ptr Str);
    other.items = arr_copy(other.items);
    foreach(other.items, item, {
        if *item == "." or *item == "" {}
        else if *item == ".." and !!arr_len(self.items) arr_pop(self.items)
        else arr_push(self.items, *item);
    });
    return self;
}

func Path Path_div_ptr_char(Path self, ptr char _other) {
    Path other = _other;
    return self / other;
}

func Path Path_div_Str(Path self, ptr char _other) {
    Path other = _other;
    return self / other;
}

func void Path_assign_Str(ptr Path self, Str path_str) {
    Path new;
    path_str.replace(str("\\"), str("/"));
    new.items = path_str.split(str("/"));
    *self = *self / new;
}

func void Path_assign_ptr_char(ptr Path self, ptr char path_cstr) {
    Path_assign_Str(self, str(path_cstr));
}

func Str Str_when_Path(Path self) {
    return str_join(str(OS_PATH_DELIMITER), self.items);
}

func void Printer_when_Path(ptr void _, Path p) {
    for(i=0, i<arr_len(p.items), ++i, {
        item = p.items[i];
        if i print(OS_PATH_DELIMITER);
        print(item);
    });
}
