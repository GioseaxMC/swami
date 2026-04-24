include {
    "stdlib.sw",
    "files.sw",
    "json.sw",
}

func int main()
{   
    json = js_parse_string("{\"people\": [{\"name\" : \"Giose\", \"age\" : 18 }]}", "string");

    if !(e=json_get_many(&json, ["people", "[0]"])) 
        return 1;
    
    if !(e=json_get(e, "name"))
        return 1;

    println(e.str);
    
    json_print(&json);

    json_free(&json);
    return 0;
}
