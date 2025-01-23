declare void @printf(i8*, ...)
define void @print(i8* %1) { call void (i8*, ...) @printf(i8* %1) ret void }
define void @println(i8* %2) { call void (i8*, ...) @printf(i8* %2) call void @printf(i8* @newl) ret void }

@newl = constant [2 x i8] c"\0A\00"
@format_int = constant [3 x i8] c"%i\00"

; int x = 0;
; x += 3;
; printf("$i\n", x);

define i64 @main(  ) {
  %integer = alloca i64
  store i64 0, ptr %integer
  %number = load i64, ptr %integer
  %sum = add i64 %number, 3
  store i64 %sum, ptr %integer
  %printer = load i64, ptr %integer
  %iformat = load ptr, ptr @format_int
  call void (i8*, ...) @printf(ptr %iformat, i64 %printer)
  ret  i64 0  
}
