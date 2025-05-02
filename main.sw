include ( "string.sw" )

macro da_array(type, name) {
    struct name {
        ptr type items,
        int count,
        int length,
    };
}

da_array(int, integers)

func int main() {
    

    return 0;
}
