include { "stdlib.sw" }

struct Person {
    ptr char name,
    int age,
}

func Person person_init(int age, ptr char name) {
    Person person;
    person.name = name;
    person.age = age;
    person;
}

func void main() {
    
    people = [
        person_init(18, "Giose"),
        person_init(69, "Freezah"),
        person_init(102, "Plaiboy Carti"),
    ];

    for (i=0, i<lambda_len(people, $.age), i++, {
        printf("Person %i:\n  name : %s\n  age  : %i\n\n", i+1, people[i]);
    });
}
