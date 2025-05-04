# Swami
## Desc
A low level, compiled language written in python
## Goals
- [x] Convenient
- [x] Statically typed
- [ ] Turing Completeness (it is, but i didn't prove it yet)
- [ ] Self Hosted
- [ ] Natively compiled
## Dependencies
- Clang's LLVM
- Any C target (such as mingw32 or msvc)
## How to use
### File: main.sw
```c
extern void printf(ptr char, <>)

func int main() {
    printf("Hello World!\n");

    return 0;
}
```
### Run:
```
$ python swami.py main.sw -o main
$ main

Hello World!
```
### Simple cat implementation: cat.sw
```rs
include { "stdlib.sw" };

func int main(int argc, ptr ptr char argv) {
  int i = 1;
  ptr char contents;
  int size;
  while (i < argc) {
    contents = read_file(argv[i], &size);
    printf("%s\n", contents);
    i++;
  }
  return 0;
}
```
### Run:
```
$ python swami.py cat.sw -o cat
$ cat main.sw

extern void printf(ptr char, <>)

func int main() {
    printf("Hello World!\n");

    return 0;
}
```