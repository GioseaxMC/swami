include "stdlib.sw";

func void main(int argc, ptr argv) {
	int idx = 0;
	while (idx < argc) {
		println(p_read(argv, idx))
		idx++;
	}
	return;
}