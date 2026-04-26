include {
    "stdlib.sw"
}


func int main()
{

    struct Val {
        int a,
    };
    t = func int two() { 2; };

    list = [
        1, t(), 3, 4
    ];

    for(i=0, list[i], ++i, {
        println(list[i]);
    });
}
