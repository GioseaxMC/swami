include "stdlib.sw";

struct Person {
    str name;
    int age;
}

func void main() {
    Person person;

    person.age = 17;
    person.name = 0;

    printf("%i", person.age)
    println("")
    printf("%s", person.name)
    

    return;
}



