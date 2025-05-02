extern void printf(ptr char, <>)
extern ptr void malloc(int)

struct Person {
    ptr char name,
    int age,
}

func void main(int argc, ptr ptr char argv) {

    int sizeof_Person = 8*2;

    ptr Person people = malloc(sizeof_Person * 2);

    people[0].name = "Giose";
    people[0].age = 17;
    
    people[1].name = "Rick";
    people[1].age = 18;

    printf("%s is %i years old.\n", people[0].name, people[0].age++);
    printf("%s is %i years old.\n", people[0].name, ++people[0].age);
    
    printf("%s is %i years old.\n", people[1].name, people[1].age++);
    printf("%s is %i years old.\n", people[1].name, ++people[1].age);

    return;
}




