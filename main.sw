include {
    "stdlib.sw"
}

func int main() {

    println("Hello", "World");

    unroll (,) (+) { # what
        println(67, 420, 1);
    };
}
