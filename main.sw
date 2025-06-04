include { "stdlib.sw", "surl.sw" }

func int main() {

    surl_init(0);
    
    ptr char buffer;
    
    surl_fetch("https://raw.githubusercontent.com/GioseaxMC/swami/refs/heads/main/main.c", buffer, {
        printf("fetching failed\n");
        return 1;
    });

    printf("contents:\n\n%s", buffer);

    surl_close();
    return 0;
}


