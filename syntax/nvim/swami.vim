syntax keyword swamiType int char ptr <> bool void

syntax match swamiNumber /\<\d\+\>/
syntax keyword swamiKeyword TODO return func type struct if else while for foreach extern include macro cast as sizeof param panic reserve break continue
syntax match swamiString /"\v([^"\\]|\\.)*"/ 
syntax match swamiString /'\v([^'\\]|\\.)*'/
syntax match swamiComment "#.*$"
syntax match swamiCompiler "@\w\+"

highlight link swamiString String
highlight link swamiType Type
highlight link swamiNumber Number
highlight link swamiKeyword Keyword
highlight link swamiComment Comment
highlight link swamiCompiler SpecialComment
