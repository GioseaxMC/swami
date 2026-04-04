include {
    "stdlib.sw",
    "etonizer.sw",
    "files.sw"
}

func int main()
{
    f = read_file("dummy.json");
    if f.error return 1;
    tokens = tokenize(f.contents, f.filename);
    
    while more(tokens) {
        t = consume(tokens); 
        println(t.token);
    });

    free_file(f);
    free_token_list(tokens);

    println("Hello world");
}
