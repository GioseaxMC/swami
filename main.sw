include "stdlib.sw";

struct Person {
    str name;
    int age;
}

func void main(int argc, ptr argv) {
    Person person;

    person.age = 17;
    person.name = "GIOSE";

    printf("%i", person.age)
    println("")
    printf("%s", person.name)
    

    return;
}