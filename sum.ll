declare void @printf(i8*, ...)
define void @print(i8* %1) { call void (i8*, ...) @printf(i8* %1) ret void }
define void @println(i8* %2) { call void (i8*, ...) @printf(i8* %2) call void @printf(i8* @newl) ret void }

@newl = constant [2 x i8] c"\0A\00"
@format_int = constant [3 x i8] c"%i\00"
@str64 = constant [7 x i8] c"call64\00"
@str32 = constant [7 x i8] c"call32\00"

define i64 @add_64_ptr_ptr (ptr %one, ptr %two) {
  %1 = load i64, ptr %one
  %2 = load i64, ptr %two
  %3 = add i64 %1, %2
  call void @printf(i8* @str64)
  ret i64 %3
}

define i32 @add_32_ptr_ptr (ptr %one, ptr %two) {
  %1 = load i32, ptr %one
  %2 = load i32, ptr %two
  %3 = add i32 %1, %2
  call void @printf(i8* @str32)
  ret i32 %3
}


define i64 @main(  ) {
  %number1_64 = alloca i64
  %number2_64 = alloca i64
  %number1_32 = alloca i32
  %number2_32 = alloca i32
  store i64 641, ptr %number1_64
  store i64 642, ptr %number2_64
  store i32 321, ptr %number1_32
  store i32 322, ptr %number2_32

  %result64 = call i64 @add_64_ptr_ptr(i64* %number1_64, i64* %number2_64)
  %result32 = call i32 @add_32_ptr_ptr(i32* %number1_32, i32* %number2_32)

  %result64_str = inttoptr i64 %result64 to i8*
  %result32_str = inttoptr i32 %result32 to i8*

  call void @println(i8* %result64_str)
  call void @println(i8* %result32_str)

  ret i64 0
}
