include { "stdlib.sw", "dicts.sw" }

dictionary(int, StrInt)

extern void printf(ptr char, <>)

func int main(int argc, ptr ptr char argv) {
    dt_make(StrInt, months);

    dt_add(months, "january", 1);
    dt_add(months, "june", 6);
    dt_add(months, "february", 2);
    
    printf("june is the %i'th month of the year\n", dt_get(months, "june"));
    printf("february is the %i'th month of the year\n", dt_get(months, "february"));

    return 0;
}





