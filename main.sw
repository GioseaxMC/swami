include {
    "stdlib.sw",
}

struct Test {
    int number,
}

func Test Test_new(ptr Test self) {
    assert(!self, "cannot initialize from created type");

    Test new;
    new;
}

func int main ()
{
    t = Test.new();
    
    t = t.new();
    println(t.number);
}

