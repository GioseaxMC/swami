extern void printf(ptr char, <>)
extern ptr void malloc(int)

struct Person {
    ptr char name,
    int age,
}

func void main(int argc, ptr ptr char argv) {

    int sizeof_Person = 8*2;

    Person people;
    people.name = "Giose";
    people.age = 17;

    printf("%s is %i years old.\n", people.name, people.age);
    printf("%s is %i years old.\n", people.name, people.age);

    return;
}