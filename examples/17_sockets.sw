include {
    "stdlib.sw",
    "threads.sw"
}

extern int socket(i16, i16, int)
extern i16 htons(int)
extern void bind(int, ptr void, int)
extern void listen(int, int)
extern int accept(int, ptr void, ptr void)
extern void recv(int, ptr char, int, int)
extern void send(int, ptr char, int)

i16 AF_INET = 2;
i16 SOCK_STREAM = 1;
i32 INADDR_ANY = 0;

struct Addr_in {
    i32 s_addr,
}

struct Addr {
    i16 sin_family,
    i16 sin_port,
    Addr_in sin_addr,
    i64 sin_zero,
}

func void worker() {
    for(i=0, i<100, i++, {
        printf("Worker %i\n", i);
    });
}

func int main() {

    t = _makeThread(worker, NULL);
    printf("Later\n");
    for(i=0, i<100, ++i, {
        printf("mainer: %i\n", i);
    });
    
    _waitAndClose(t, NULL);

    return 0;

    Addr address;
    addrlen = sizeof(address);
    reserve 1024 as buffer;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    
    PORT = 6767;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    bind(server_fd, &address, sizeof(address));
    listen(server_fd, 0);

    printf("Server listening on port %i...\n", PORT);

    client_fd = accept(server_fd, &address, &addrlen);
    
    recv(client_fd, buffer, 1024, 0);
    printf("Client says: %s\n", buffer);

    send(client_fd, buffer, strlen(buffer));
}
