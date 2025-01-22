declare void @printf(i8*, ...)
define void @print(i8* %1) { call void (i8*, ...) @printf(i8* %1) ret void }
define void @println(i8* %2) { call void (i8*, ...) @printf(i8* %2) call void @printf(i8* @newl) ret void }

@string.1 = constant [12 x i8] c"Hello World\00"
@newl = constant [2 x i8] c"\0A\00"
  
define i64 @main(  ) {
  call void @println(  i8* @string.1  )
  ret  i64 0  
}
