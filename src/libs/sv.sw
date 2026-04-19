include {
    "stdlib.sw",
}

struct StringView {
    ptr char cstr,
    int len,
}

func StringView sv_from_parts(ptr char cstr, int len) {
    StringView s;
    s.len = len;
    s.cstr = cstr;
    return s;
}

func StringView sv(ptr char str) {
    sv_from_parts(str, strlen(str));
}

func void StringView_assign_ptr_char(ptr StringView _sv, ptr char cstr) {
    *_sv = sv(cstr);
}

func StringView sv_lchop(StringView sv, int n) {
    if n > sv.len n = sv.len;
    sv.cstr = op_ptr(sv.cstr,+,n);
    sv.len = sv.len-n;
    sv;
}

func StringView sv_rchop(StringView sv, int n) {
    if n > sv.len n = sv.len;
    sv.len = sv.len-n;
    sv;
}

func StringView sv_ltrim(StringView sv) {
    while sv.len != 0 && isspace(*sv.cstr)
        sv = sv_lchop(sv, 1);
    sv;
}

func StringView sv_rtrim(StringView sv) {
    while sv.len != 0 && isspace(sv.cstr[sv.len-1])
        sv = sv_rchop(sv, 1);
    sv;
}

func StringView sv_trim(StringView sv) {
    sv = sv_ltrim(sv);
    sv = sv_rtrim(sv);
}

func StringView sv_chop_by_type(ptr StringView sv, bool (char) ptr istype) {
    int i = 0;
    while (i<sv.len && !istype(sv.cstr[i])) {
        i++;
    };

    if (i < sv.len) {
        StringView result;
        result.cstr = sv.cstr;
        result.len = i;
        *sv = sv_lchop(*sv, i+1);
        return result;
    };

    StringView result = *sv;
    *sv = sv_lchop(*sv, sv.len);
    return result;
}

func StringView sv_chop_by_delim(ptr StringView sv, char delim) {
    int i = 0;
    while (i<sv.len && sv.cstr[i] != delim) {
        i++;
    };

    if (i < sv.len) {
        StringView result;
        result.cstr = sv.cstr;
        result.len = i;
        *sv = sv_lchop(*sv, i+1);
        return result;
    };

    StringView result = *sv;
    *sv = sv_lchop(*sv, sv.len);
    return result;
}

func void sv_print(StringView sv) {
    printf("%.*s", sv.len, sv.cstr);
}

func void sv_println(StringView sv) {
    sv_print(sv);
    printf("\n");
}

func void Printer_when_StringView(ptr void _, StringView sv) {
    sv_print(sv);
}

func ptr char sv_to_cstr(StringView sv) {
    ptr char cstr = malloc(sv.len+1);
    memcpy(cstr, sv.cstr, sv.len);
    cstr[sv.len] = 0;
    return cstr;
}

func bool sv_eq(StringView a, StringView b) {
    if a.len != b.len return 0;
    for(i=0, i<a.len, i++, {
        if a.cstr[i] != b.cstr[i] return 0;
    });
    return 1;
}

func StringView sv_chop_suffix(StringView sv, StringView suffix) {
    if suffix.len > sv.len return sv;

    test = sv;
    test.cstr = op_ptr(test.cstr,+,sv.len-suffix.len);
    test.len = suffix.len;

    if !sv_eq(test, suffix) return sv;
    
    sv.len = sv.len-suffix.len;

    return sv;
}

func StringView sv_chop_prefix(StringView sv, StringView prefix) {
    if prefix.len > sv.len return sv;

    test = sv;
    test.len = prefix.len;

    if !sv_eq(test, prefix) return sv;

    sv.len = sv.len-prefix.len;
    sv.cstr = op_ptr(sv.cstr,+,prefix.len);

    return sv;
}
