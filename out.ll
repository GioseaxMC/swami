; FILE: main.sw

declare void @printf(i8*, ...)
define void @print(i8* %1) { call void (i8*, ...) @printf(i8* %1) ret void }
define void @println(i8* %2) { call void (i8*, ...) @printf(i8* %2) call void @printf(i8* @newl) ret void }

@str.1 = constant [18 x i8] c"the number is: %i\00"
@str.1.ptr = global ptr @str.1
@newl = constant [2 x i8] c"\0A\00"

define i64 @main() {
  %number = alloca i64
  %3 = add i64 256, 0
  %4 = add i64 2, 0
  %5 = mul i64 %4, %3
  %6 = add i64 2, 0
  %7 = mul i64 %6, %5
  store i64 %7, ptr %number
  %8 = load ptr, ptr @str.1.ptr
  %9 = load i64, ptr %number
  call void @printf(i8* %8, i64 %9)
  %10 = add i64 0, 0
  ret  i64 %10
}
