include {
    "stdlib.sw",
    "socket.sw"
}

func int main()
{
    s = socket(AF_INET, SOCK_STREAM, 0);

    addr = get_addr("0.0.0.0", 6767);

    bind(s, &addr, sizeof(addr));

    listen(s, 16);

    reserve 1024 as buf;

    while 1 {
        c = accept(s, NULL, NULL);

        while 1 {
            n = recv(c, buf, 1024, 0);
            buf[n] = 0;

            println("ECHOING: ", buf);

            if n<=0 break;

            send(c,buf,n,0);
        };

        closesocket(c);
    };
}
