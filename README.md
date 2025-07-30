# Swami
## Desc
A low level, compiled language written in python
## Goals
- [x] Convenient
- [x] Statically typed
- [x] Turing Completeness (see examples/09_rule_110.sw)
- [ ] Self Hosted
- [ ] Natively compiled
## Dependencies
- Clang's LLVM
- Any C target (such as mingw32 or msvc)
## How to use
### File: main.sw
```c
include { "stdlib.sw" }

func int main() {
    printf("Hello World!\n");
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
include {
    "stdlib.sw",
    "files.sw",
}

func int main(int argc, ptr ptr char argv) {
  
  for(i=1, i<argc, i++, {
    
    contents = read_file(argv[i]).contents;
    printf("%s\n", contents);

  });
  
  return 0;
}
```
### Run:
```
$ python swami.py cat.sw -o cat
$ cat main.sw

include { "stdlib.sw" }

func int main() {
    printf("Hello World!\n");
}

```
