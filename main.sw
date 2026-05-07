include {
    "stdlib.sw",
    "darrays.sw",
    "strings.sw",
}

func int main ()
{
    strings = new_array_with_gc(Str);
    
    rule ss 67;

    Str a = str(ss);

    arr_push(strings, a);
    arr_push(strings, a);
    arr_push(strings, a);
    arr_push(strings, a);  
    
    Str c = str_join(str("."), strings);
    
    println(c);

    sigmas = str(str_split(c, str(".")));
    sigmas = str(">> ") + sigmas;

    println(sigmas);
}
