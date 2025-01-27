intern int r_int(ptr, int)
llvm "define i64 @r_int(ptr %base_ptr, i64 %offset) {";
llvm "  %offset_ptr = getelementptr i64, ptr %base_ptr, i64 %offset";
llvm "  %value = load i64, ptr %offset_ptr";
llvm "  ret i64 %value";
llvm "}";

intern ptr r_ptr(ptr, int)
llvm "define ptr @r_ptr(ptr %base_ptr, i64 %offset) {";
llvm "  %offset_ptr = getelementptr ptr, ptr %base_ptr, i64 %offset";
llvm "  %value = load ptr, ptr %offset_ptr";
llvm "  ret ptr %value";
llvm "}";

intern char r_chr(ptr, int)
llvm "define i8 @r_chr(ptr %base_ptr, i64 %offset) {";
llvm "  %offset_ptr = getelementptr i8, ptr %base_ptr, i64 %offset";
llvm "  %value = load i8, ptr %offset_ptr";
llvm "  ret i8 %value";
llvm "}";

intern void w_int(ptr, int)
llvm "define void @w_int(ptr %base_ptr, i64 %value) {";
llvm "  store i64 %value, ptr %base_ptr";
llvm "  ret void";
llvm "}";

intern void w_ptr(ptr, ptr)
llvm "define void @w_ptr(ptr %base_ptr, ptr %value) {";
llvm "  store ptr %value, ptr %base_ptr";
llvm "  ret void";
llvm "}";

intern void w_chr(ptr, char)
llvm "define void @w_chr(ptr %base_ptr, i8 %value) {";
llvm "  store i8 %value, ptr %base_ptr";
llvm "  ret void";
llvm "}";

intern ptr ptradd(ptr, int)
llvm "define ptr @ptradd(ptr %p, i64 %offset) {";
llvm "  %result = getelementptr i8, ptr %p, i64 %offset";
llvm "  ret ptr %result";
llvm "}";
llvm "";