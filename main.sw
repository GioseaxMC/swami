include {
    "stdlib.sw",
}

add = func int => (int a, int b) {
    a+b;
}

func void main ()
{

    println(add(6,7));
}
