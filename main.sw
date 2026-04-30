include {
    "stdlib.sw"
}

func int main()
{
    i64 x = 2;
    for (i=0, i<64, i++, {
        println(x = x*x);
    });
}
