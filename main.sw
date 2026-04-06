include {
    "stdlib.sw",
    "files.sw",
    "json.sw",
}

func int main()
{   
    f = read_file("dummy.json");
    json = js_parse_string(f.contents, f.filename);
        
    num = json_get(json, "nest ok [2]").str;    
    println(num);

    return 0;
}
