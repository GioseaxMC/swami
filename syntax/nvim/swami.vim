"match known types
syntax keyword swamiType int char ptr bool void i64 i32 i16

"match sybols
syntax match swamiVariable /\v<[A-Za-z_][A-Za-z0-9_]*>/

"match struct Type
syntax match swamiKeyword /\<struct\>/ nextgroup=swamiType skipwhite
syntax match swamiType /[A-Za-z_][A-Za-z0-9_]*/ contained

"match keyboards
syntax keyword swamiKeyword TODO return func type if else while for foreach extern include macro cast as sizeof param panic reserve break continue

"match Types with CamelCase
syntax match swamiType /\<[A-Z][A-Za-z0-9_]*\>/

" Functions: word followed by (
syntax match swamiFunction /\<[A-Za-z_][A-Za-z0-9_]*\s*(/hs=s,he=e-1

"match misc
syntax match swamiConstant /\<[A-Z][A-Z0-9_]*\>/
syntax match swamiNumber /\<\d\+\>/
syntax match swamiString /"\v([^"\\]|\\.)*"/ 
syntax match swamiComment "#.*$"
syntax match swamiCompiler "@\w\+"

"LINKING PARKS HELL YEAHAHSJKJHAKS
highlight link swamiString String
highlight link swamiType Type
highlight link swamiNumber Number
highlight link swamiConstant Number
highlight link swamiKeyword Keyword
highlight link swamiComment Comment
highlight link swamiCompiler SpecialComment
highlight link swamiVariable Identifier
highlight link swamiFunction Function
