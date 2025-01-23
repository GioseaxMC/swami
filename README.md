# Swami
## Desc
A low level, compiled language written in python
## Goals
- [ ] Statically typed
- [ ] Turing Completeness
- [ ] Self Hosted
- [ ] Natively compiled
- [ ] Convenient
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
```bash
$ python swami.py main.sw -o main
$ main
Hello World!
```
