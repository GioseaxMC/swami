

include {
    "stdlib.sw"
}

struct String {
    ptr char cstr,
    int len,
    int cap,
}

func String String_call(String str, ptr char cstr, int len) {
    str.cstr = cstr;
    str.len = len;
    str.cap = len;
    str;
}

func void Printer_when_String(ptr void _, String self) {
    printf("%.*s", self.len, self.cstr);
}

func void main()
{
    str = (String)("Hello There", 11);
    
    println(str);
}
