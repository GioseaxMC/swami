import os
from dataclasses import dataclass
from sys import *
from colorama import Fore as f
from pprint import pp
argc = len(argv)

def rgb_text(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

iota_counter = 0
def iota(reset: int = 0):
    global iota_counter
    if reset != -1:
        iota_counter += 1
    if reset == 1:
        iota_counter = 0
    return iota_counter

DEBUGGING = "-d" in argv
parse_indentation = 0
def debug(*args, **kwargs) -> None:
    if not DEBUGGING:
        return
    print(rgb_text(75,75,75)+"│ "*(parse_indentation+1)+f.RESET, end="")
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

def compiler_error(node, prompt, errno = -1):
    token = node.token
    print(get_tk_pos(token)+":", "ERROR:", prompt.replace("&t", token[-1]))
    with open(token[0], "r") as fp:
        content = fp.read()
        print("\n  "+content.split("\n")[token[1]])
        print("  "+" "*token[2]+"^")
        print("  "+" "*token[2]+"| here")
    if errno:
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
    "++",
    "--",
    "!",
    "==",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "&",
    ".",
    "<>",
    "["
]

human_unarys = [
    "+",
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
            # debug(f"CHECKING LINE: '{line[idx:idx+2]}'")
            if line[idx:idx+2] in human_operands:
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
        self.name = ""

    def tkname(self):
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
    VARDECL = iota()
    VARREF = iota()
    INC = iota()
    DEC = iota()
    UNARY = iota()
    PTREF = iota()
    GETPTR = iota()

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
    "var declaration",
    "var reference",
    "increment",
    "decrement",
    "unary",
    "pointer reference",
    "get pointer",

    "null",
]

declared_funcs = {}
func_namespaces = {}
global_vars  = {}
declared_strings = []
all_declared_vars = []

current_namespace: dict[str, Node]

def add_usr_var(node):
    global global_vars, all_declared_vars, current_namespace
    if parse_indentation:
        debug("[USINGNAMESPACE]: current_namespace")
        namespace = current_namespace
    else:
        debug("[USINGNAMESPACE]: global_vars")
        namespace = global_vars
    if node.tkname() in namespace:
        parser_error(node.token, "Redeclaration of variable '&t'")
    namespace[node.tkname()] = node
    all_declared_vars.append(node.tkname())

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
    
    def goback(self):
        self.set(self.pointer-1)

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
        case "=": return 1
        case "+": return 2
        case "-": return 2
        case "*": return 3
        case "/": return 3
        case "[": return 4

        case _:   return 0

def print_node(node):
    if not DEBUGGING:
        return
    print(f"[ <{human_kind[node.kind][:3]}>: {node.tkname()} ", end="")
    # for arg in node.args:
    #     print(arg.token[-1])
    for idx, arg in enumerate(node.args):
        if idx:
            print(", ", end="")
        else:
            print(" ", end="")
        print_node(arg)
    if node.block:
        print_node(node.block)
    print(f" </{human_kind[node.kind][:3]}> ]", end="")

nodes = list()

def parse():
    global parse_indentation
    parse_indentation = 0
    while tokens.more():
        if (node:=parse_primary()).kind != kind.NULL:
            nodes.append(node)

def parse_type(ptrl):
    typename = tokens.consume()
    if typename[-1] not in human_type:
        parser_error(typename, "Expected typename but got '&t'")
    rtype = human_type.index(typename[-1])
    if rtype == sw_type.VOID:
        if ptrl:
            rtype = sw_type.CHAR
        return rtype, ptrl
    elif rtype == sw_type.PTR:
        return parse_type(ptrl+1)
    else:
        return rtype, ptrl

def parse_named_arg():
    node = Node()
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    node.name = node.tkname()
    debug("[NAMEDARG]:", node.tkname())
    add_usr_var(node)
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
    global current_namespace, parse_indentation
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    declared_funcs[node.tkname()] = node
    func_namespaces[node.tkname()] = {}
    current_namespace = func_namespaces[node.tkname()]
    debug("[FUNCDESC]", node.tkname(), ":", hlt(node.type, node.ptrl))
    tokens.expect("(")
    parse_indentation += 1
    node.args = parse_named_args()
    parse_indentation -= 1
    node.block = parse_block()
    current_namespace = global_vars
    
def parse_funcall(node):
    debug("[FUNCALL]:", node.tkname())
    called = declared_funcs[node.tkname()]
    tokens.expect("(")
    node.type, node.ptrl = called.type, called.ptrl
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
    debug("[EXTERN]: name:", node.tkname(), rlt(node.type, node.ptrl))
    declared_funcs[node.tkname()] = node
    tokens.expect("(")
    node.args = parse_unnamed_args()

def parse_vardecl(node):
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    add_usr_var(node)
    debug("[VARDECL]:", node.tkname())
    if tokens.current()[-1] == "=":
        tokens.consume()
        node.block = parse_expression(0)

def parse_varref(node):
    if node.tkname() in current_namespace:
        namespace = current_namespace
    else:
        namespace = global_vars
    var_info = namespace[node.tkname()]
    debug("[VARREF]:", node.name)
    node.type, node.ptrl = var_info.type, var_info.ptrl
    if tokens.current()[-1] == "++":
        node.block = Node()
        node.block.token = tokens.consume()
        node.block.kind = kind.INC

def parse_primary():
    token = tokens.consume()
    debug(F"[PRIMARY]: '{token[-1]}'")
    node = Node()
    node.token = token

    if token[-1].isnumeric():
        node.kind = kind.NUM_LIT
        
    elif represents_string(token[-1]):
        node.kind = kind.STR_LIT
        escaped_string = llvm_escape(node.tkname())
        if escaped_string not in declared_strings:
            declared_strings.append(llvm_escape(node.tkname()))
        node.val = declared_strings.index(escaped_string)
        
    elif token[-1] in human_unarys:
        debug("[UNARYFOUND]")
        node.kind = kind.UNARY
        node.block = parse_primary()
        
    elif token[-1] == "(":
        node.kind = kind.EXPRESSION
        node.args.append(parse_expression(0))
        tokens.expect(")")
    
    elif token[-1] == "{":
        node.kind = kind.BLOCK
        node = parse_block()
    
    elif token[-1] == "&":
        node.kind = kind.GETPTR
        node.block = parse_primary()
        node.type = node.block.type
        node.ptrl = node.block.ptrl+1

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

    elif token[-1] == "++":
        node.kind = kind.INC
        node.block = Node()
        node.block.kind = kind.VARREF
        node.block.token = tokens.consume()
        parse_varref(node.block)
        node.type, node.ptrl = node.block.type, node.block.ptrl

    elif token[-1] in human_type:
        node.kind = kind.VARDECL
        tokens.goback()
        parse_vardecl(node)

    elif token[-1] in all_declared_vars:
        node.kind = kind.VARREF
        parse_varref(node)

    elif token[-1] in declared_funcs:
        node.kind = kind.FUNCCALL
        parse_funcall(node)

    else:
        node.kind = kind.NULL
    return node

def parse_expression(importance): # <- wanted to write priority
    global parse_indentation; parse_indentation += 1
    node = parse_primary()
    while tokens.more() and get_importance(tokens.current()) > importance and tokens.current()[-1] in human_operands:
        debug("[parsing tk]", tokens.current())
        op_token = tokens.consume()
        op_node = Node()
        op_node.token = op_token
        op_node.kind = kind.OPERAND
        op_node.type, op_node.ptrl = node.type, node.ptrl
        op_node.args.append(node)
        right_node = parse_expression(get_importance(op_token))
        op_node.args.append(right_node)
        if op_node.tkname() == "[":
            tokens.expect("]")
        node = op_node
    
    parse_indentation += -1
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
    if DEBUGGING:
        print()

def sizeof(type: int, ptrl: int): # in bytes please
    debug(rlt(type, ptrl))
    debug({(type, ptrl)})
    if ptrl:
        return 8
    match type:
        case sw_type.PTR:
            return 8
        case sw_type.INT:
            return 8
        case sw_type.VOID:
            return 0
        case sw_type.CHAR:
            return 1
        case sw_type.BOOL:
            return 1
    return -1

def cast(src, src_type, src_ptrl, dest_type, dest_ptrl, level):
    typecmp = bool(src_ptrl) - bool(dest_ptrl) # > 0 
    isptr = src_ptrl or dest_ptrl
    bothp = src_ptrl and dest_ptrl
    if (src_type, src_ptrl) == (dest_type, dest_ptrl):
        debug("Not casting, cuz same")
        return iota(-1), dest_type, dest_ptrl
    if bothp:
        out_writeln(f"%{iota()} = bitcast {rlt(src_type, src_ptrl)} {src} to {rlt(dest_type, dest_ptrl)}", level)
    elif isptr:
        if typecmp > 0:
            out_writeln(f"%{iota()} = ptrtoint {rlt(src_type, src_ptrl)} {src} to {rlt(dest_type, dest_ptrl)}", level)
        else:
            out_writeln(f"%{iota()} = inttoptr {rlt(src_type, src_ptrl)} {src} to {rlt(dest_type, dest_ptrl)}", level)
    else:
        if dest_type == sw_type.BOOL:
            out_writeln(f"%{iota()} = icmp ne {rlt(src_type, src_ptrl)} {src}, 0", level)
        else:
            if sizeof(dest_type, dest_ptrl) > sizeof(src_type, src_ptrl):
                out_writeln(f"%{iota()} = zext {rlt(src_type, src_ptrl)} {src} to {rlt(dest_type, dest_ptrl)}", level)
            elif sizeof(dest_type, dest_ptrl) < sizeof(src_type, src_ptrl):
                out_writeln(f"%{iota()} = trunc {rlt(src_type, src_ptrl)} {src} to {rlt(dest_type, dest_ptrl)}", level)
            else:
                out_writeln(f"%{iota()} = bitcast {rlt(src_type, src_ptrl)} {src} to {rlt(dest_type, dest_ptrl)}", level)
    return iota(-1), dest_type, dest_ptrl #iota -1 : casted val

def compile_debug(func):
    def wrapper(*args, **kwargs):
        ret = func(*args, *kwargs)
        if DEBUGGING:
            out_writeln(f"; compiled node with kind: {human_kind[args[0].kind]} :: {rlt(args[0].type, args[0].ptrl)}", args[1])
        return ret
    return wrapper

@compile_debug
def compile_node(node, level, assignable = 0):
    nlevel = level+1
    arg_names = []
    debug("[COMPILING]:", human_kind[node.kind])
    match node.kind:
        case kind.EXPRESSION:
            for arg in node.args:
                arg_names.append(compile_node(arg, level))
                node.type, node.ptrl = arg.type, arg.ptrl
            return f"{arg_names[-1]}"

        case kind.RET:
            for arg in node.args:
                argn = compile_node(arg, level)
            if len(node.args):
                out_writeln(f"ret {rlt(node.args[-1].type, node.args[-1].ptrl)} {argn}", level)
            else:
                out_writeln("ret void", level)
        
        case kind.BLOCK:
            for arg in node.args:
                compile_node(arg, level)

        case kind.STR_LIT:
            node.type = sw_type.CHAR
            node.ptrl = 1
            return f"@str.{node.val}"

        case kind.NUM_LIT:
            node.type = sw_type.INT
            node.ptrl = 0
            return f"{node.tkname()}"
                
        case kind.UNARY:
            result = compile_node(node.block, level)
            node.type, node.ptrl = node.block.type, node.block.ptrl
            if node.tkname() == "-":
                if node.block.kind == kind.NUM_LIT:
                    result = "-"+result
                    return result
                else:
                    out_writeln(f"%{iota()} = sub {rlt(node.block.type, node.block.ptrl)} 0, {result}", level)
            else:
                return result

        case kind.VARDECL:
            if level:
                out_writeln(f"%{node.tkname()} = alloca {rlt(node.type, node.ptrl)}", level)
                if node.block:
                    to_assign = compile_node(node.block, level)
                    if node.block.ptrl and node.ptrl and node.type == sw_type.CHAR:
                        out_writeln(f"store ptr {to_assign}, ptr %{node.tkname()}", level)
                    elif node.block.kind != kind.NUM_LIT and (node.type, node.ptrl) != (node.block.type, node.block.ptrl):
                        compiler_error(node, f"Types don't match in assignment '{hlt(node.type, node.ptrl)}' != '{hlt(node.block.type, node.block.ptrl)}'")
                    elif node.block.kind == kind.NUM_LIT:
                        out_writeln(f"store {rlt(node.type, 0)} {to_assign}, ptr %{node.tkname()}", level)
                    else:
                        out_writeln(f"store {rlt(node.type, node.ptrl)} {to_assign}, ptr %{node.tkname()}", level)
                    # out_writeln(f"store {rlt(node.type, node.ptrl)} {to_assign}, ptr %{node.tkname()}", level)
            else:
                if node.block.kind == kind.NUM_LIT:
                    argn = compile_node(node.block, level)
                if node.ptrl:
                    out_writeln(f"@{node.tkname()} = global {rlt(node.type, node.ptrl)} null", level)
                else:
                    out_writeln(f"@{node.tkname()} = global {rlt(node.type, node.ptrl)} {argn}", level)

        case kind.VARREF:
            if assignable:
                node.ptrl += 1
                if node.tkname() in global_vars:
                    return f"@{node.tkname()}"
                else:
                    return f"%{node.tkname()}"
            else:
                if node.tkname() in global_vars:
                    out_writeln(f"%{iota()} = load {rlt(node.type, node.ptrl)}, ptr @{node.tkname()}", level)
                else:
                    out_writeln(f"%{iota()} = load {rlt(node.type, node.ptrl)}, ptr %{node.tkname()}", level)
                return_iota = iota(-1)
                if node.block:
                    if node.block.kind == kind.INC:
                        out_writeln(f"%{iota()} = add {rlt(node.type, node.ptrl)} %{iota(-1)-1}, 1", level)
                        if node.tkname() in global_vars:
                            out_writeln(f"store {rlt(node.type, node.ptrl)} %{iota(-1)}, ptr @{node.tkname()}", level)
                        else:
                            out_writeln(f"store {rlt(node.type, node.ptrl)} %{iota(-1)}, ptr %{node.tkname()}", level)
                return f"%{return_iota}"
        
        case kind.INC:
            if node.block.tkname() in global_vars:
                out_writeln(f"%{iota()} = load {rlt(node.block.type, node.block.ptrl)}, ptr @{node.block.tkname()}", level)
            else:
                out_writeln(f"%{iota()} = load {rlt(node.block.type, node.block.ptrl)}, ptr %{node.block.tkname()}", level)
            out_writeln(f"%{iota()} = add {rlt(node.block.type, node.block.ptrl)} %{iota(-1)-1}, 1", level)
            if node.block.tkname() in global_vars:
                out_writeln(f"store {rlt(node.block.type, node.block.ptrl)} %{iota(-1)}, ptr @{node.block.tkname()}", level)
            else:
                out_writeln(f"store {rlt(node.block.type, node.block.ptrl)} %{iota(-1)}, ptr %{node.block.tkname()}", level)
            return f"%{iota(-1)}"

        case kind.OPERAND:
            if node.tkname() == "=":
                dest_node = node.args[0]
                src_node = node.args[1]
                if dest_node.tkname() in global_vars:
                    dest = f"@{dest_node.tkname()}"
                else:
                    dest = f"{compile_node(dest_node, level, 1)}"
                debug(f"[OPERAND]: source node is of kind {human_kind[src_node.kind]}")
                src = compile_node(src_node, level)
                if src_node.ptrl and dest_node.ptrl and dest_node.type == sw_type.CHAR:
                    out_writeln(f"store ptr {src}, ptr {dest}", level)
                elif src_node.kind != kind.NUM_LIT and (src_node.type, src_node.ptrl) != (dest_node.type, dest_node.ptrl):
                    compiler_error(node, f"Types don't match in assignment '{hlt(dest_node.type, dest_node.ptrl)}' != '{hlt(src_node.type, src_node.ptrl)}'")
                elif src_node.kind == kind.NUM_LIT:
                    out_writeln(f"store {rlt(dest_node.type, 0)} {src}, ptr {dest}", level)
                else:
                    out_writeln(f"store {rlt(dest_node.type, dest_node.ptrl)} {src}, ptr {dest}", level)
                    
                return src
            elif node.tkname() == "[":
                dest_node = node.args[0]
                src_node = node.args[1]
                if dest_node.kind == kind.EXPRESSION:
                    for arg in node.args:
                        arg_names.append(compile_node(arg, level))
                    out_writeln(f"%{iota()} = load {rlt(dest_node.type, dest_node.ptrl)}, ptr {arg_names[0]}", level)
                    out_writeln(f"%{iota()} = getelementptr {rlt(dest_node.type, dest_node.ptrl)}, ptr %{iota(-1)-1}, i32 {arg_names[1]}", level)
                else:
                    src = compile_node(node.args[1], level)
                    out_writeln(f"%{iota()} = load {rlt(dest_node.type, dest_node.ptrl)}, ptr %{dest_node.tkname()}", level)
                    out_writeln(f"%{iota()} = getelementptr {rlt(dest_node.type, dest_node.ptrl)}, ptr %{iota(-1)-1}, i32 {src}", level)
                if not assignable:
                    out_writeln(f"%{iota()} = load {rlt(dest_node.type, dest_node.ptrl-1)}, ptr %{iota(-1)-1}", level)
                    node.type, node.ptrl = dest_node.type, dest_node.ptrl-1
                else:
                    node.type, node.ptrl = dest_node.type, dest_node.ptrl
                return f"%{iota(-1)}"
                    
            else:
                dest_node = node.args[0]
                src_node = node.args[1]
                for idx, arg in enumerate(node.args):
                    arg_names.append(compile_node(arg, level))
                    if not idx:
                        node.ptrl, node.type = arg.ptrl, arg.type # operand type is type of the first operand
                match node.tkname():
                    case "+":
                        out_writeln(f"%{iota()} = add {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "-":
                        out_writeln(f"%{iota()} = sub {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "*":
                        out_writeln(f"%{iota()} = mul {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "/":
                        out_writeln(f"%{iota()} = sdiv {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"

        case kind.GETPTR:
            node.kind = node.block.kind
            name = compile_node(node.block, level, 1)
            return f"{name}"

        case kind.EXTERN:
            out_write(f"declare {rlt(node.type, node.ptrl)} @{node.tkname()}(", level)
            for idx, arg in enumerate(node.args):
                if idx:
                    out_write(", ", 0)
                out_write(rlt(arg.type, arg.ptrl), 0)
            out_writeln(")\n", 0)
        
        case kind.FUNCCALL:
            funcinfo = declared_funcs[node.tkname()]
            for arg in node.args:
                arg_names.append(compile_node(arg, level))
            if (funcinfo.type, funcinfo.ptrl) == (sw_type.VOID, 0):
                out_write(f"call void @{node.tkname()}(", level); iota()
            else:
                out_write(f"%{iota()} = call {rlt(funcinfo.type, funcinfo.ptrl)} @{node.tkname()}(", level)
            for idx, arg in enumerate(arg_names):
                if idx:
                    out_write(", ", 0)
                out_write(f"{rlt(node.args[idx].type, node.args[idx].ptrl)} {arg}", 0)
            out_writeln(")", 0)
        
        case kind.FUNCDECL:
            global iota_counter
            iota_counter = -1
            out_write(f"define {rlt(node.type, node.ptrl)} @{node.tkname()}(", level)
            for idx, arg in enumerate(node.args):
                if idx:
                    out_write(", ", 0)
                out_write(f"{rlt(arg.type, arg.ptrl)} %{iota()}", 0)
            out_writeln(") {", 0)
            iota_counter = -1
            for arg in node.args:
                out_writeln(f"%{arg.tkname()} = alloca {rlt(arg.type, arg.ptrl)}", nlevel)
                out_writeln(f"store {rlt(arg.type, arg.ptrl)} %{iota()}, ptr %{arg.tkname()}", nlevel)
            iota()
            compile_node(node.block, nlevel)
            out_writeln("}\n", 0)
        
        case _:
            compiler_error(node, "Unexpected unqualified token '&t'")
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