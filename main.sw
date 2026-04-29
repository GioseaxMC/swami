include {
    "stdlib.sw",
}

func void main()
{
    add = func int => (int a, int b) { a+b; };

    println(add(6,7));
}
