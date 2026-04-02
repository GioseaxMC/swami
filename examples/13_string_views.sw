include {
    "stdlib.sw",
    "sv.sw"
}

func int main() {
    s = sv("The fox jumps over a frog or something\n");
    s = sv_trim(s);

    s = sv_chop_prefix(s, sv("The"));
    s = sv_chop_suffix(s, sv("something"));

    s = sv_trim(s);
    sv_println(s);
}
