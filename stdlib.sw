intern int i_read(ptr, int)
llvm "define i64 @i_read(ptr %base_ptr, i64 %offset) {";
llvm "  %offset_ptr = getelementptr i64, ptr %base_ptr, i64 %offset";
llvm "  %value = load i64, ptr %offset_ptr";
llvm "  ret i64 %value";
llvm "}";

intern ptr p_read(ptr, int)
llvm "define ptr @p_read(ptr %base_ptr, i64 %offset) {";
llvm "  %offset_ptr = getelementptr ptr, ptr %base_ptr, i64 %offset";
llvm "  %value = load ptr, ptr %offset_ptr";
llvm "  ret ptr %value";
llvm "}";

intern char c_read(ptr, int)
llvm "define i8 @c_read(ptr %base_ptr, i64 %offset) {";
llvm "  %offset_ptr = getelementptr i8, ptr %base_ptr, i64 %offset";
llvm "  %value = load i8, ptr %offset_ptr";
llvm "  ret i8 %value";
llvm "}";

intern ptr ptradd(ptr, int)
llvm "define ptr @ptradd(ptr %p, i64 %offset) {";
llvm "  %result = getelementptr i8, ptr %p, i64 %offset";
llvm "  ret ptr %result";
llvm "}";