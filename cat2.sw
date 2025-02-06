include "stdlib.sw";

func int main(int argc, ptr ptr char argv) {
  int i = 1;
  ptr char contents;
  int size;
  while (i < argc) {
    contents = read_file(argv[i], &size);
    println(contents)
    i++;
  }
  return 0;
}