# socket.sw

@windows param "-lws2_32"

struct InAddr { i32 s_addr };

struct SockAddr_in {
    i16 sin_family,
    i16 sin_port,
    InAddr sin_addr,
    i64 sin_zero,
};

i32 AF_INET = 2;
i32 SOCK_STREAM = 1;
i32 INADDR_ANY = 0;

i16 AF_INET_FAMILY = 2;

i16 WSA_VERSION = 514;

# TODO: handle number of arguments for send and recv, see if default linux need flags

@linux extern i32 socket(i32, i32, i32);
@linux extern i32 bind(i32, ptr SockAddr_in, i32);
@linux extern i32 listen(i32, i32);
@linux extern i32 accept(i32, ptr SockAddr_in, ptr i32);
@linux extern i32 recv(i32, ptr char, i32, i32);
@linux extern i32 send(i32, ptr char, i32, i32);
@linux extern i32 close(i32);
@linux extern i32 connect(i32, ptr SockAddr_in, i32);

@windows extern int socket(i32, i32, i32);
@windows extern i32 bind(int, ptr SockAddr_in, i32);
@windows extern i32 listen(int, i32);
@windows extern int accept(int, ptr SockAddr_in, ptr i32);
@windows extern i32 recv(int, ptr char, i32, i32);
@windows extern i32 send(int, ptr char, i32, i32);
@windows extern i32 connect(int, ptr SockAddr_in, i32);
@windows extern i32 closesocket(int);

@linux macro closesocket(__s) { close(__s); }

extern i16 htons(i16);
extern void inet_pton(i32, ptr char, ptr InAddr);

func SockAddr_in get_addr(ptr char ip, int port)
{
    SockAddr_in addr;
    addr.sin_family = AF_INET_FAMILY;
    addr.sin_port = htons(cast port as i16);
    inet_pton(AF_INET, ip, &addr.sin_addr);
    return addr;
}

@windows extern void WSACleanup();
@windows extern void WSAStartup(i16, ptr void);

@windows construct {
    reserve 1024 as __wsa_data;
    WSAStartup(WSA_VERSION, __wsa_data);
    at_exit(WSACleanup);
}
