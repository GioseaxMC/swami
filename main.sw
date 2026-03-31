include {
    "stdlib.sw"
}

struct Simple {
    int x
}

macro get_header(p) {{ (cast op_ptr(p,+,0) as ptr Simple); }; }
macro get_x(p) {{ get_header(p).x; }; }

func int main() {
    Simple x;
    ptr Simple px = &x;
    
    printf("lets try\n");
    
    px.x = 4;

    min(3,2);

    printf("%p\n", &(px.x));

    min(1,2);

    printf("%p\n", &(get_header(px).x));
}
