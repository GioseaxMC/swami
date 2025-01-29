include "stdlib.sw";

struct Person {
    int age;
    ptr char name;
}

func void main() {
    ptr Person persons = cast(ptr Person, malloc(2*sizeof(Person)));

    persons[0].name = "Giose";
    persons[0].age = 17;
    persons[1].name = "Gabry";
    persons[1].age = 15;

    int idx = 0;
    while (idx < 2) {
        println(persons[idx].name);
        printf("%i", persons[idx].age);
        println("");
        idx++;
    }

    return;
}


