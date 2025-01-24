; FILE: main.sw

declare void @printf(i8*, ...)
define void @print(i8* %1) { call void (i8*, ...) @printf(i8* %1) ret void }
define void @println(i8* %2) { call void (i8*, ...) @printf(i8* %2) call void @printf(i8* @newl) ret void }

@str.1 = constant [3 x i8] c"%i\00"
@str.1.ptr = global ptr @str.1
@newl = constant [2 x i8] c"\0A\00"
@iota_counter = global i64 0

define i64 @iota() {
  %1 = bitcast ptr @iota_counter to ptr
  %2 = load i64, ptr %1
  %3 = bitcast ptr @iota_counter to ptr
  %4 = load i64, ptr %3
  %5 = add i64 1, 0
  %6 = add i64 %5, %4
  store i64 %6, ptr %1
  %7 = bitcast ptr @iota_counter to ptr
  %8 = load i64, ptr %7
  ret  i64 %8
}

define i64 @main() {
  %9 = call i64 @iota()
  %10 = call i64 @iota()
  %11 = call i64 @iota()
  %12 = call i64 @iota()
  %13 = call i64 @iota()
  %14 = call i64 @iota()
  %var = alloca i64
  %15 = call i64 @iota()
  store i64 %15, ptr %var
  %16 = load ptr, ptr @str.1.ptr
  %17 = bitcast ptr %var to ptr
  %18 = load i64, ptr %17
  call void @printf(i8* %16, i64 %18)
  %19 = add i64 0, 0
  ret  i64 %19
}
