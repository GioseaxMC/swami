include {
    "stdlib.sw",
    "socket.sw"
}

func int main()
{
    s = socket(AF_INET, SOCK_STREAM, 0);

    addr = get_addr("127.0.0.1", 6767);
    
    r = connect(s, &addr, sizeof(addr));
    if r<0 {
        println("Couldn't connect");
        return 1;
    };

    reserve 1024 as buf;

    while 1 {
        l = read(0, buf, 1024);
        if l<=0 break;
        buf[l] = 0;

        send(s, buf, l, 0);

        n = recv(s, buf, 1024, 0);
        buf[n] = 0;

        println("RECEIVED: ", buf);
    };

    closesocket(s);
}
