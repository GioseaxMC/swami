
include {
    "stdlib.sw",
    "dicts.sw",
}

func int main()
{
    ht = new_ht(ptr ptr int);
    
    *ht_get(ht, "ages") = new_ht(int);
    *ht_get(ht, "heights") = new_ht(int);
    

    *ht_get(*ht_get(ht, "ages"), "giose") = 18;
    *ht_get(*ht_get(ht, "heights"), "giose") = 182;
    *ht_get(*ht_get(ht, "ages"), "giose") = 17;

    ht_foreach(ht, k, i, {
        ht_foreach(*i, key, item, {
            println(k, " > ", key, " > ", *item);
        });
        ht_free(*i);
    });

    ht_free(ht);

}
