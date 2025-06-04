link "curl"

extern ptr void curl_easy_init()
extern int curl_global_init(int)
extern int curl_easy_setopt(ptr void, int, <>)
extern int curl_easy_perform(ptr void)
extern void curl_easy_cleanup(ptr void)
extern void curl_global_cleanup()

extern ptr void malloc(int)
extern ptr void memcpy(ptr void, ptr void, int)

int CURLOPT_WRITEDATA = 10001
int CURLOPT_URL = 10002
int CURLOPT_WRITEFUNCTION = 20011

int CURL_GLOBAL_DEFAULT = 3

func int curl_write_tobuff(ptr char p, int size, int count, ptr ptr char userdata) {
    int total = count * size;

    *userdata = malloc(total + 1);
    if (!*userdata) {
        return 0;
    };
    memcpy(*userdata, p, total);
    *userdata[total] = 0;
    
    return total;

}

macro surl_init(at_fail) {{
    int __code = curl_global_init(CURL_GLOBAL_DEFAULT);
    if ( __code ) { at_fail; };
};}

macro surl_fetch(url, buffer, at_fail) {{
    ptr void __curl = curl_easy_init();
    if ( !__curl ) { at_fail; };
    curl_easy_setopt(__curl, CURLOPT_URL, url);
    curl_easy_setopt(__curl, CURLOPT_WRITEFUNCTION, curl_write_tobuff);
    curl_easy_setopt(__curl, CURLOPT_WRITEDATA, &buffer);
    curl_easy_perform(__curl);
    curl_easy_cleanup(__curl);
    buffer;
};}

macro surl_close() {
    curl_global_cleanup();
}

