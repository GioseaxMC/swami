; file: main.sw

declare void @printf(i8*, ...)
define void @print(i8* %1) { call void (i8*, ...) @printf(i8* %1) ret void }
define void @println(i8* %2) { call void (i8*, ...) @printf(i8* %2) call void @printf(i8* @newl) ret void }

@str.1 = constant [17 x i8] c"Starting program\00"
@str.1.ptr = global ptr @str.1
@str.2 = constant [33 x i8] c"the age is: %i, the number is %i\00"
@str.2.ptr = global ptr @str.2
@str.3 = constant [1 x i8] c"\00"
@str.3.ptr = global ptr @str.3
@str.4 = constant [17 x i8] c"program finished\00"
@str.4.ptr = global ptr @str.4
@newl = constant [2 x i8] c"\0A\00"

define i64 @main() {
  %3 = load ptr, ptr @str.1.ptr
  call void @println(i8* %3)
  %age = alloca i64
  store i64 21, ptr %age
  %number = alloca i64
  store i64 128, ptr %number
  %4 = load ptr, ptr @str.2.ptr
  %5 = load i64, ptr %age
  %6 = load i64, ptr %number
  call void @printf(i8* %4, i64 %5, i64 %6)
  %7 = load ptr, ptr @str.3.ptr
  call void @println(i8* %7)
  %8 = load ptr, ptr @str.4.ptr
  call void @println(i8* %8)
  %9 = add i64 0, 0
  ret  i64 %9
}
