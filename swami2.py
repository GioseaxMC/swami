import os
from dataclasses import dataclass
from sys import *
argc = len(argv)

iota_counter = 0
def iota(reset: int = 0):
    global iota_counter
    if reset != -1:
        iota_counter += 1
    if reset == 1:
        iota_counter = 0
    return iota_counter

DEBUGGING = "-d" in argv
debug_level = 0
def debug(*args, **kwargs) -> None:
    if not DEBUGGING:
        return
    print(": "*debug_level, end="")
    print(*args, **kwargs)

@dataclass
class sw_type:
    PTR  = iota(1)
    INT  = iota()
    VOID = iota()
    CHAR = iota()
    BOOL  = iota()
    ANY = iota()

human_type = [
    "ptr",
    "int",
    "void",
    "char",
    "bool",
    "<>",
]

llvm_type = [
    "ptr",
    "i64",
    "void",
    "i8",
    "i1",
    "...",
]

def rlt(type: int, ptr_level: int):
    return llvm_type[type] + ("*"*ptr_level)

def hlt(type: int, ptr_level: int):
    return ("ptr "*ptr_level) + human_type[type]

def parser_error(token, prompt, errno = -1):
    print(get_tk_pos(token)+":", "ERROR:", prompt.replace("&t", token[-1]))
    with open(token[0], "r") as fp:
        content = fp.read()
        print("\n  "+content.split("\n")[token[1]])
        print("  "+" "*token[2]+"^")
        print("  "+" "*token[2]+"| here")
    if errno:
        exit(errno)

def compiler_error(state, prompt, errno = -1):
    ogToken = state.ogToken
    assert ogToken, "IS NONE"
    if state.lastToken:
        lastToken = state.lastToken
    else:
        state.ogToken = ogToken
    print(get_tk_pos(ogToken)+":", "ERROR:", prompt.replace("&t", ogToken[-1]))
    with open(ogToken[0], "r") as fp:
        content = fp.read()
        debug("ogToken:", ogToken)
        debug("lastToken:", lastToken)
        print("\n  "+content.split("\n")[ogToken[1]])
        print("  "+" "*ogToken[2]+"^"*(lastToken[2] - ogToken[2] + 1))
        print("  "+" "*ogToken[2]+"| here")
    exit(errno)

def get_tk_name(token: tuple[str, int, int, str]):
    return token[-1]

def get_tk_pos(token: tuple[str, int, int, str]):
    return token[0]+":"+str(token[1]+1)+":"+str(token[2]+1)

human_operands = [
    "=",
    "+",
    "-",
    "*",
    "/",
    "!",
    "++",
    "--",
    "==",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "&",
    ".",
    "<>"
]

human_unarys = [
    "+"
    "-"
]

def uisalnum(s: str) -> bool:
    return all(c.isalnum() or c == "_" for c in s)

def tokenizable(s: str) -> bool:
    return uisalnum(s) and not s[0].isnumeric() 

def represents_string(s:str) -> bool:
    return s[0] == "\"" and s[-1] == "\""

def llvm_escape(s: str) -> str:
    escape_map = {"n": "\\0A", "t": "\\09", "r": "\\0D", "b": "\\08", "f": "\\0C", "v": "\\0B", "'": "\\27", '"': "\\22", "\\": "\\5C"}
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            next_char = s[i + 1]
            if next_char in escape_map:
                result.append(escape_map[next_char])
                i += 1
            else:
                result.append("\\")
                result.append(next_char)
        else:
            result.append(s[i])
        i += 1
    return "".join(result)

def find_next(line: str) -> int:
    for idx, c in enumerate(line):
        if c == "\"":
            idx = line[idx+1:].find("\"")
            return max(1, idx+2)
        if c in human_operands and (idx == 0 or line[idx-1] == " "):
            if line[idx+1] in human_operands:
                return max(1, idx+2)
            return max(1, idx+1)
        if not uisalnum(c):
            return max(1, idx)
    return -1

def llvm_len(s: str) -> int:
    length = 0
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 2 < len(s) and s[i+1] in "0123456789ABCDEFabcdef":
            i += 3
        else:
            i += 1
        length += 1
    return length

def lex_tokens(line: str):
    og_len = len(line)
    while len(line) and not line.isspace():
        sline = line.lstrip()
        col = og_len - len(sline)
        x = find_next(sline)
        if x > 0:
            yield col, sline[:x]
            line = sline[x:]
        else:
            yield col, sline
            line = ""

def lex_lines(file_path: str):
    with open(file_path, "r") as fp:
        file_contents = fp.read()
    for row, line in enumerate(file_contents.split("\n")):
        for col, word in lex_tokens(line):
            yield file_path, row, col, word

class Node:
    def __init__(self):
        self.token = None
        self.val = -1
        self.kind = -1
        self.args = []
        self.type = 0
        self.ptrl = 0
        self.block = 0
    
    def name(self):
        return self.token[-1]

OUTFILE_PATH = "./main.ll"
INFILE_PATH = "./main.sw"

if argc <= 1:
    debug("swami.py : usage")
    debug("    swami [input-file] -o <output-file>")
    debug("")
    debug("  - [required argument]")
    debug("  - <optional argument> defaults to main")
    debug("")

idx = 1
while idx < argc:
    arg = argv[idx].lower()
    match arg:
        case "-o":
            idx+=1
            OUTFILE_PATH = argv[idx].removesuffix(".ll")+".ll"
        case _:
            if arg[0] != "-":
                INFILE_PATH = argv[idx].removesuffix(".sw")+".sw"
    idx+=1

@dataclass
class kind:
    NUM_LIT = iota(1)
    STR_LIT = iota()
    OPERAND = iota()
    EXPRESSION = iota()
    FUNCDECL = iota()
    FUNCCALL = iota()
    BLOCK = iota()
    EXTERN = iota()
    RET = iota()

    NULL = iota()

human_kind = [
    "number",
    "string",
    "operation",
    "expression",
    "func decl",
    "func call",
    "block",
    "extern",
    "return",

    "null",
]

declared_funcs = {}
declared_strings = []

class Manager:
    def __init__(self, items):
        self.items = items
        self.pointer = 0

    def next(self):
        self.pointer+=1
        return self.items[self.pointer]
    
    def inc(self):
        self.pointer += 1
    
    def peek(self):
        assert self.pointer+1 < len(self.items), "Cannot peek non exsisting token"
        return self.items[self.pointer+1]

    def current(self):
        return self.items[self.pointer]
    
    def consume(self):
        self.pointer+=1
        return self.items[self.pointer-1]
    
    def expect(self, str):
        res = self.consume()
        return res if res[-1] == str else parser_error(res, f"Expected '{str}' but got '&t'")

    def prev(self):
        assert self.pointer >= 0, "Negative pointer"
        return self.items[self.pointer-1]

    def more(self):
        return self.pointer < len(self.items)

    def set(self, nptr):
        self.pointer = nptr

parsed_tokens = list(lex_lines(INFILE_PATH))
debug("[PARSEDTKS]:", [tk[-1] for tk in parsed_tokens])
tokens = Manager(parsed_tokens)

def get_importance(token):
    tkname = token[-1]
    match tkname:
        case "*": return 2
        case "/": return 2
        case "+": return 1
        case "-": return 1

        case _:   return 0

def print_node(node):
    debug(f"[ <{human_kind[node.kind][:3]}>: {node.name()} ", end="")
    # for arg in node.args:
    #     debug(arg.token[-1])
    for idx, arg in enumerate(node.args):
        if idx:
            debug(", ", end="")
        else:
            debug(" ", end="")
        print_node(arg)
    if node.block:
        print_node(node.block)
    debug(f" </{human_kind[node.kind][:3]}> ]", end="")

nodes = list()

def parse():
    while tokens.more():
        if (state:=parse_primary()).kind != kind.NULL:
            nodes.append(state)

def parse_type(ptrl):
    typename = tokens.consume()
    if typename[-1] not in human_type:
        parser_error(typename, "Expected typename but got '&t'")
    rtype = human_type.index(typename[-1])
    if rtype == sw_type.PTR:
        return parse_type(ptrl+1)
    else:
        return rtype, ptrl

def parse_named_arg():
    node = Node()
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    if tokens.current()[-1] != ")":
        tokens.expect(",")
    return node

def parse_named_args():
    args = []
    while tokens.current()[-1] != ")":
        args.append(parse_named_arg())
    tokens.consume()
    return args

def parse_block():
    tokens.expect("{")
    block = Node()
    block.kind = kind.BLOCK
    block.token = tokens.prev()
    while tokens.current()[-1] != "}":
        block.args.append(parse_expression(0))
        tokens.expect(";")
    tokens.expect("}")
    return block
    
def parse_funcdecl(node):
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    declared_funcs[node.name()] = node
    debug("[FUNCDESC]", node.name(), ":", hlt(node.type, node.ptrl))
    tokens.expect("(")
    node.args = parse_named_args()
    node.block = parse_block()
    
def parse_funcall(node):
    debug("[FUNCALL]:", node.name())
    tokens.expect("(")
    while tokens.current()[-1] != ")":
        node.args.append(parse_expression(0))
        if tokens.current()[-1] != ")":
            tokens.expect(",")
    tokens.expect(")")
    
    debug("[FUNCALL]: Done")

def parse_unnamed_arg():
    node = Node()
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.prev()
    if tokens.current()[-1] != ")":
        tokens.expect(",")
    return node

def parse_unnamed_args():
    args = []
    while tokens.current()[-1] != ")":
        args.append(parse_unnamed_arg())
    tokens.expect(")")
    return args

def parse_extern(node):
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    debug("[EXTERN]: name:", node.name(), rlt(node.type, node.ptrl))
    declared_funcs[node.name()] = node
    tokens.expect("(")
    node.args = parse_unnamed_args()

def parse_primary():
    token = tokens.consume()
    debug("[TOBEPARSED]:", token[-1])
    node = Node()
    node.token = token

    if token[-1].isnumeric():
        node.kind = kind.NUM_LIT
        
    elif represents_string(token[-1]):
        node.kind = kind.STR_LIT
        node.val = len(declared_strings)
        declared_strings.append(llvm_escape(node.name()))

    elif token[-1] in human_unarys:
        node.kind = kind.OPERAND
        
    elif token[-1] == "(":
        node.kind = kind.EXPRESSION
        node.args.append(parse_expression(0))
        tokens.expect(")")
    
    elif token[-1] == "{":
        node.kind = kind.BLOCK
        node = parse_block()
        
    elif token[-1] == "func":
        node.kind = kind.FUNCDECL
        parse_funcdecl(node)

    elif token[-1] == "extern":
        node.kind = kind.EXTERN
        parse_extern(node)
    
    elif token[-1] == "return":
        node.kind = kind.RET
        if tokens.current()[-1] != ";":
            debug("[RETURN]: has args")
            node.args.append(parse_expression(0))
        else:
            debug("[RETURN]: no args")
        
    elif token[-1] in declared_funcs:
        node.kind = kind.FUNCCALL
        parse_funcall(node)

    else:
        node.kind = kind.NULL
    return node

def parse_expression(importance): # <- wanted to write priority
    node = parse_primary()
    while tokens.more() and get_importance(tokens.current()) > importance and tokens.current()[-1] in human_operands:
        debug("[parsing tk]", tokens.current())
        op_token = tokens.consume()
        op_node = Node()
        op_node.token = op_token
        op_node.kind = kind.OPERAND
        op_node.args.append(node)
        right_node = parse_expression(get_importance(op_token))
        op_node.args.append(right_node)
        node = op_node
    
    return node

parse()

out = open(OUTFILE_PATH, "w")
def out_write(content, level):
    global out
    out.write("  "*level+content)
def out_writeln(content, level):
    out_write(content, level)
    out_write("\n", 0)

for node in nodes:
    print_node(node)
    print()

def compile_node(state, level):
    nlevel = level+1
    arg_names = []
    debug("[COMPILING]:", human_kind[state.kind])
    match state.kind:
        case kind.RET:
            for arg in state.args:
                argn = compile_node(arg, level)
            if len(state.args):
                out_writeln(f"ret {rlt(state.args[-1].type, state.args[-1].ptrl)} {argn}", level)
            else:
                out_writeln("ret void", level)
        
        case kind.BLOCK:
            for arg in state.args:
                compile_node(arg, level)

        case kind.STR_LIT:
            state.type = sw_type.CHAR
            state.ptrl = 1
            return f"@str.{state.val}"

        case kind.NUM_LIT:
            state.type = sw_type.INT
            state.ptrl = 0
            return f"{state.name()}"

        case kind.OPERAND:
            for arg in state.args:
                arg_names.append(compile_node(arg, level))
                state.ptrl, state.type = arg.ptrl, arg.type
            match state.name():
                case "+":
                    out_writeln(f"%{iota()} = add {rlt(state.type, state.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    return f"%{iota(-1)}"
                case "-":
                    out_writeln(f"%{iota()} = sub {rlt(state.type, state.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    return f"%{iota(-1)}"
                case "*":
                    out_writeln(f"%{iota()} = mul {rlt(state.type, state.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    return f"%{iota(-1)}"
                case "/":
                    out_writeln(f"%{iota()} = sdiv {rlt(state.type, state.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    return f"%{iota(-1)}"

        case kind.EXTERN:
            out_write(f"declare {rlt(state.type, state.ptrl)} @{state.name()}(", level)
            for idx, arg in enumerate(state.args):
                if idx:
                    out_write(", ", 0)
                out_write(rlt(arg.type, arg.ptrl), 0)
            out_writeln(")\n", 0)
        
        case kind.FUNCCALL:
            funcinfo = declared_funcs[state.name()]
            for arg in state.args:
                arg_names.append(compile_node(arg, level))
            if (funcinfo.type, funcinfo.ptrl) == (sw_type.VOID, 0):
                out_write(f"call {rlt(funcinfo.type, funcinfo.ptrl)} @{state.name()}(", level); iota()
            else:
                out_write(f"%{iota()} = call {rlt(funcinfo.type, funcinfo.ptrl)} @{state.name()}(", level)
            for idx, arg in enumerate(arg_names):
                if idx:
                    out_write(", ", 0)
                out_write(f"{rlt(state.args[idx].type, state.args[idx].ptrl)} {arg}", 0)
            out_writeln(")", 0)
        
        case kind.FUNCDECL:
            iota(1)
            out_write(f"define {rlt(state.type, state.ptrl)} @{state.name()}(", level)
            for idx, arg in enumerate(state.args):
                if idx:
                    out_write(", ", 0)
                out_write(f"{rlt(arg.type, arg.ptrl)} %{iota()}", 0)
            out_writeln(") {", 0)
            iota(1)
            for arg in state.args:
                out_writeln(f"%{arg.name()} = alloca {rlt(arg.type, arg.ptrl)}", nlevel)
                out_writeln(f"store {rlt(arg.type, arg.ptrl)} %{iota()}, ptr %{arg.name()}", nlevel)
            compile_node(state.block, nlevel)
            out_writeln("}\n", 0)
    return f"%{iota(-1)}"


def compile_nodes(nodes):
    iota(1)
    for node in nodes:
        compile_node(node, 0)

iota(1)
for string in declared_strings:
    out_writeln(f"@str.{iota()-1} = global [{llvm_len(string)-1} x i8] c\"{string[1:-1]}\\00\"", 0)
out_writeln("", 0)

compile_nodes(nodes)

out.close()

os.system(f"clang {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module -target x86_64-64w-mingw32")