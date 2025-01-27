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
func int main() {
  println("Hello World!")
  return 0;
}
```
### Commands:
```
$ python swami.py main.sw -o main
$ main
Hello World!
```
