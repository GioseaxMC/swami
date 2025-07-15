include { "stdlib.sw" }

int RULE = 110
int BufferSize = 100
ptr char top
ptr char bottom

macro init() {{
    reserve 100 as atop;
    top = atop;
    reserve 100 as abottom;
    bottom = abottom;

    memset(top, 0, 100);
    memset(bottom, 0, 100);
    top[100-1] = 1;
};}

func int pow(int base, int power) {
    if !power return 1;
    done = base;
    i = power;
    while --i {
        done = done*base;
    };
    return done;
}

func int get_cell(int idx) {
    return cast (idx > 0 && idx < BufferSize) && cast top[idx] as bool as int;
}

func int calculate_cell(int idx) {
    int power = (
        get_cell(idx-1) * 4 +
        get_cell(idx+0) * 2 +
        get_cell(idx+1) * 1
    );
    return (RULE / pow(2, power) ) & 1;
}

func void calculate_bottom() {
    for(i=99, i>=0, i--, {
        bottom[i] = cast calculate_cell(i) as char;
    });
}

func void show() {
    for(i=0, i<100, i++, {
        printf("%s ", { sign = " "; if top[i] sign = "#"; sign; });
    });
    printf("\n");
}

func void swap() {
    temp = top;
    top = bottom;
    bottom = temp;
}

func int main() {
    init();

    for(i=0, i<100, i++, {
        calculate_bottom();
        show();
        swap();
    });
}
