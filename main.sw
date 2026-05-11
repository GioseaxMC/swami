include {
    "stdlib.sw",
    "paths.sw"
}

func int main() {
    Path p = "../this/is/a/../an/example/path";
    
    p = p / "../test";
    p = p / "../ok?";

    println(p);
}
