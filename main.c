#include <stdio.h>
#define CURL_STATICLIB
#include <curl/curl.h>

int main(void) {
    curl_global_init(CURL_GLOBAL_DEFAULT);  // <-- important on some systems
    
    printf("int CURL_GLOBAL_DEFAULT = %i", CURL_GLOBAL_DEFAULT);

    CURL *curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to init curl\n");
        return 1;
    }

    curl_easy_setopt(curl, CURLOPT_URL, "https://example.com");
    curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    curl_global_cleanup(); // optional

    return 0;
}
