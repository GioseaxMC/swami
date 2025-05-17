# TODO: implement token level parentesis stack check

import os
from pathlib import Path
from dataclasses import dataclass
from sys import *
from colorama import Fore as f
from pprint import pp
argc = len(argv)

import argparse

cwd = Path(os.getcwd())
libs = Path(os.path.realpath(__file__)).parent / "libs"

parser = argparse.ArgumentParser(description="Swami compiler:\n\tusage: <python> swami.py main.sw -o main")

parser.add_argument('--backend', default="clang", help="the language backend to use to compile llvm (default clang)")
parser.add_argument('-d', action='store_true', help="Enable debug mode")

parser.add_argument('sourcecode', help="The swami file")

parser.add_argument('-o', help="The output file for both the .ll file and the executable", required=1)

parser.add_argument('--bflags', help="Custom flags directly passed to the backend", default="")

args = parser.parse_args()

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

parse_indentation = 0

DEBUGGING = args.d

def debug(*children, **kwchildren) -> None:
    if not DEBUGGING:
        return
    print(rgb_text(75,75,75)+"│ "*(parse_indentation+1)+f.RESET, end="")
    print(*children, **kwchildren)

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
    print(get_tk_pos(token)+":", "ERROR:" if errno else "WARNING:", prompt.replace("&t", token[-1]))
    with open(token[0], "r") as fp:
        content = fp.read()
        print("\n  "+content.split("\n")[token[1]])
        print("  "+" "*token[2]+"^")
        print("  "+" "*token[2]+"| here")
    if errno:
        # if DEBUGGING:
        #     tokens.pointer -= 1;
        #     for i in range(10):
        #         print(tokens.consume())
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
    "|",
    "||",
    "&",
    "&&",
    ".",
    "<>",
    "[",
]

human_unarys = [
    "+",
    "-",
    "!",
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
            to_search = line[idx+1:]
            for j in range(len(to_search)):
                c = to_search[j]
                if c == "\"":
                    if to_search[j-1] != "\\":
                        return max(1, j+2)
        if c == '#':
            return -2
        if c in human_operands and (idx == 0 or line[idx-1] == " "):
            # debug(f"CHECKING LINE: '{line[idx:idx+2]}'")
            if line[idx:idx+2] in human_operands:
                return max(1, idx+2)
            return max(1, idx+1)
        if not uisalnum(c):
            return max(1, idx)
    return -1

def lex_tokens(line: str):
    og_len = len(line)
    while len(line) and not line.isspace():
        sline = line.lstrip()
        col = og_len - len(sline)
        x = find_next(sline)
        if x == -2:
            break
        if x > 0:
            yield col, sline[:x]
            line = sline[x:]
        else:
            yield col, sline
            line = ""

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

def lex_lines(file_contents, file_path):
    for row, line in enumerate(file_contents.split("\n")):
        for col, word in lex_tokens(line):
            yield file_path, row, col, word

pr_cmp = {
    "(":")",
    "[":"]",
    "{":"}", }
def get_purified_tokens(file_contents, file_path):
    p_tokens = list(lex_lines(file_contents, file_path))
    pr_stack = []
    for tk in p_tokens:
        if tk[-1] in ("{", "[", "("):
            pr_stack.append(tk)
        elif tk[-1] in ("}", "]", ")"):
            if pr_cmp[pr_stack[-1][-1]] != tk[-1]:
                parser_error(pr_stack[-1], "Invalid parentesis pairing starting from here")
            else:
                pr_stack.pop()
    return p_tokens

class Node:
    def __init__(self):
        self.token = None
        self.val = -1
        self.kind = -1
        self.children = []
        self.type = -1
        self.ptrl = -1
        self.block = 0
        # self.name = ""

    def find_by_name(self, name, node):
        for idx, arg in enumerate(self.children):
            if arg.tkname() == name:
                return idx
        compiler_error(node, f"'{name}' is not an attribute for '{self.tkname()}'")

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


OUTFILE_PATH = args.o.removesuffix(".ll")+".ll"
INFILE_PATH = args.sourcecode.removesuffix(".sw")+".sw"

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
    STRUCT = iota()
    IF = iota()
    
    WHILE = iota()
    WORD = iota()
    SEMI = iota()
    
    MACRODECL = iota()
    CAST = iota()
    SIZEOF = iota()

    REFPTR = iota()
    TYPE = iota()

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
    "struct",
    "if",
    
    "while",
    "word",
    "semicolon",
    
    "macro declaration",
    "cast",
    "sizeof",

    "reference pointer",

    "null",
]

declared_funcs = {}
func_namespaces = {}
global_vars  = {}
declared_strings = []
all_declared_vars = []
declared_structs = {}
macro_tokens: dict[list[tuple]] = {}
declared_macros: dict[Node] = {}

current_namespace = global_vars

def add_usr_var(node):
    global global_vars, all_declared_vars, current_namespace
    if parse_indentation:
        debug("[USINGNAMESPACE]: current_namespace")
        namespace = current_namespace
    else:
        debug("[USINGNAMESPACE]: global_vars")
        namespace = global_vars
    exists = 0
    if node.tkname() in namespace:
        exists = 1
    namespace[node.tkname()] = node
    all_declared_vars.append(node.tkname())
    return exists

class Manager:
    def __init__(self, items):
        self.items = items
        self.items.append(
            (
                items[-1][0],
                items[-1][1],
                items[-1][2] + len(items[-1][-1]),
                "<EOT> -> end of tokens"
            )
        )
        self.pointer = 0
        self.assumed = []

    def next(self):
        self.pointer+=1
        return self.items[self.pointer]
    
    def inc(self):
        self.pointer += 1
    
    def peek(self):
        assert self.pointer+1 < len(self.items)-1, "Cannot peek non exsisting token"
        return self.items[self.pointer+1]

    def current(self):
        return self.items[self.pointer]
    
    def consume(self):
        self.pointer+=1
        return self.items[self.pointer-1]
    
    def assume(self, str):
        self.assumed.append(str)

    def goback(self):
        self.set(self.pointer-1)

    def expect(self, str):
        if len(self.assumed):
            if str == (x := self.assumed.pop()):
                return self.current()
            else:
                parser_error(self.current(), f"Assumed '{x}' looking for '{str}' but got '&t'")
        else:
            res = self.consume()
            return res if res[-1] == str else parser_error(res, f"Expected '{str}' but got '&t'")

    def prev(self):
        assert self.pointer >= 0, "Negative pointer"
        return self.items[self.pointer-1]

    def more(self):
        return self.pointer < len(self.items)-1

    def set(self, nptr):
        self.pointer = nptr

try:
    with open(INFILE_PATH, "r") as fp:
        source_codents = fp.read()
except:
    print("ERROR: failed to open input file:", INFILE_PATH)
    exit(-1)

parsed_tokens = get_purified_tokens(source_codents, INFILE_PATH)
debug("[PARSEDTKS]:", [tk[-1] for tk in parsed_tokens])
tokens = Manager(parsed_tokens)

def get_importance(token):
    tkname = token[-1]
    match tkname:
        case "=": return 1
        
        case "|": return 3
        case "&": return 4
        case "||": return 5
        case "&&": return 6
        

        case "<": return 8
        case ">": return 8
        case "<=": return 8
        case ">=": return 8
        case "==": return 8
        case "!=": return 8

        
        case "[": return 9

        case "+": return 10
        case "-": return 10
        case "*": return 11
        case "/": return 11

        case ".": return 12

        case _:   return 0

def iprint(indent, *children, **kwchildren):
    print("| "*indent, *children, *kwchildren)

def print_node(node, indent = 0):
    nindent = indent+1
    if not DEBUGGING:
        return
    iprint(indent, "name::", node.tkname())
    iprint(indent, "kind::", human_kind[node.kind])
    iprint(indent, "type::", hlt(node.type, node.ptrl))
    for arg in node.children:
        print_node(arg, nindent)
    if node.block:
        iprint(indent, "block: ")
        print_node(node.block, nindent)

def check_global(node, level):
    not_global = kind.IF, kind.WHILE, kind.RET
    _global = kind.FUNCDECL, kind.EXTERN, kind.STRUCT, kind.MACRODECL
    if level:
        if node.kind in _global:
            compiler_error(node, "the '&t' instruction can only be used at a global level")
    else:
        if node.kind in not_global:
            compiler_error(node, "the '&t' instruction cannot be used at a global (and so static) level")

nodes = list()

def parse():
    global parse_indentation
    parse_indentation = 0
    while tokens.more():
        if (node:=parse_primary()).kind != kind.NULL:
            nodes.append(node)

def parse_incdec():
    node = 0
    debug("parsing incdec", tokens.current()[-1])
    if tokens.current()[-1] == "++":
        node = Node()
        node.token = tokens.consume()
        node.kind = kind.INC
    elif tokens.current()[-1] == "--":
        node = Node()
        node.token = tokens.consume()
        node.kind = kind.DEC
    return node

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

def parse_named_arg(closer):
    node = Node()
    node.type, node.ptrl = parse_type(0)
    if node.type != sw_type.ANY:
        node.token = tokens.consume()
        node.name = node.tkname()
        if not tokenizable(node.tkname()):
            parser_error(node.token, "Invalid name for argument")
    else:
        node.token = tokens.current()
    debug("[NAMEDARG]:", node.tkname())
    if tokens.current()[-1] != closer:
        tokens.expect(",")
    return node

def parse_named_args(closer):
    children = []
    while tokens.current()[-1] != closer:
        children.append(parse_named_arg(closer))
    tokens.expect(closer)
    return children

def parse_untyped_arg(closer):
    node = Node()
    node.token = tokens.consume()
    node.name = node.tkname()
    if not tokenizable(node.tkname()):
        parser_error("Invalid name for argument")
    debug("[NAMEDARG]:", node.tkname())
    if tokens.current()[-1] != closer:
        tokens.expect(",")
    return node

def parse_untyped_args(closer):
    children = []
    while tokens.current()[-1] != closer:
        children.append(parse_untyped_arg(closer))
    tokens.expect(closer)
    return children

def parse_macro_tokens():
    body_tokens = []
    macro_parsing_level = 0
    m_parsing = 1
    tokens.expect("{")
    debug("starting macro tokens parsing from", tokens.current())
    while m_parsing:
        token = tokens.consume()
        tkname = token[-1]
        debug("[MACRO]: parsing", tkname)
        if tkname == "{":
            macro_parsing_level+=1
        if tkname == "}":
            if macro_parsing_level:
                macro_parsing_level-=1
                body_tokens.append(token)
            else:
                m_parsing = 0
        else:
            body_tokens.append(token)
    return body_tokens

def parse_macro_decl():
    node = Node()
    node.token = tokens.consume()
    tokens.expect("(")
    node.children = parse_untyped_args(")")
    macro_tokens[node.tkname()] = parse_macro_tokens()
    declared_macros[node.tkname()] = node
    return node

def parse_macro_args():
    body_tokens = []
    m_level = 0
    running = 1
    while running:
        token = tokens.consume()
        tkname = token[-1]
        debug("[MACROARG]: parsing", tkname, "with indentation", m_level)
        if tkname in ("(", "{"): # check for macro related bugs
            m_level+=1
        if tkname in (")", "}"):
            if m_level:
                m_level-=1
                body_tokens.append(token)
            else:
                tokens.pointer -= 1 # no one will see this shit
                running = 0
        elif tkname == "," and not m_level: 
            tokens.pointer -= 1 # no one will see this shit
            running = 0
        else:
            body_tokens.append(token)
    return body_tokens

def parse_macro_call():
    global tokens, parse_indentation
    node = Node()
    node.token = tokens.prev()
    macro_args = []
    tokens.expect("(")
    while tokens.current()[-1] != ")":
        debug("macro-token-before:", tokens.current()[-1])
        macro_args.append(parse_macro_args())
        debug("macro-token-after:", tokens.current()[-1])
        if tokens.current()[-1] != ")":
            tokens.expect(",")
    tokens.expect(")")

    if len(macro_args) != len(declared_macros[node.tkname()].children):
        compiler_error(node, f"Expected {len(declared_macros[node.tkname()].children)} tokens but got {len(macro_args)}")

    current_macro_tks = macro_tokens[node.tkname()].copy() # memcopy or da_copy()
    arg_names = [x.tkname() for x in declared_macros[node.tkname()].children]

    for idx, arg in enumerate(current_macro_tks):
        debug(idx, arg)
        if arg[-1] in arg_names:
            arg_idx = arg_names.index(arg[-1])
            current_macro_tks.pop(idx)
            debug(macro_args)
            for tki, tk in enumerate(macro_args[arg_idx]):
                debug("--", idx, tk)
                current_macro_tks.insert(idx+tki, tk)

    og_tokens = tokens

    if DEBUGGING:
        for tk in current_macro_tks:
            debug("..", tk)
    tokens = Manager(current_macro_tks)

    debug("starting macro manager from:", tokens.current())
    old_pi = parse_indentation
    parse_indentation = -1
    while tokens.more():

        debug("parsing macro_body:", tokens.current())
        node.children.append(parse_expression(0))
        tokens.expect(";")
        
    parse_indentation = old_pi

    tokens = og_tokens
    return node;

def parse_block():
    tokens.expect("{")
    block = Node()
    block.token = tokens.current()
    block.kind = kind.BLOCK
    while tokens.current()[-1] != "}":
        block.children.append(parse_expression(0))
        tokens.expect(";")
    tokens.expect("}")
    return block
    
def parse_funcdecl(node):
    global current_namespace, parse_indentation
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    if not tokenizable(node.tkname()):
        parser_error(node.token, "Invalid function name")
    declared_funcs[node.tkname()] = node
    func_namespaces[node.tkname()] = {}
    current_namespace = func_namespaces[node.tkname()]
    debug("[FUNCDESC]", node.tkname(), ":", hlt(node.type, node.ptrl))
    tokens.expect("(")
    parse_indentation += 1
    node.children = parse_named_args(")")
    for arg in node.children:
        add_usr_var(arg)
    parse_indentation -= 1
    node.block = parse_block()
    current_namespace = global_vars

def parse_funcall(node):
    debug("[FUNCALL]:", node.tkname())
    called = declared_funcs[node.tkname()]
    tokens.expect("(")
    node.type, node.ptrl = called.type, called.ptrl
    while tokens.current()[-1] != ")":
        node.children.append(parse_expression(0))
        if tokens.current()[-1] != ")":
            tokens.expect(",")
    tokens.expect(")")
    
    debug("[FUNCALL]: Done")

def parse_unnamed_arg(closer):
    node = Node()
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.prev()
    if tokens.current()[-1] != closer:
        tokens.expect(",")
    return node

def parse_unnamed_args(closer):
    children = []
    while tokens.current()[-1] != closer:
        children.append(parse_unnamed_arg(closer))
    return children

def parse_extern(node):
    node.type, node.ptrl = parse_type(0)
    node.token = tokens.consume()
    if node.tkname() in declared_funcs:
        node.kind = kind.NULL
    debug("[EXTERN]: name:", node.tkname(), rlt(node.type, node.ptrl))
    declared_funcs[node.tkname()] = node
    tokens.expect("(")
    node.children = parse_unnamed_args(")")
    tokens.expect(")")

def parse_struct(node):
    node.token = tokens.consume()
    debug(f"[STRUCT]: {node.tkname()}")
    human_type.append(node.tkname())
    llvm_type.append(f"%struct.{node.tkname()}")
    tokens.expect("{")
    node.children = parse_named_args("}")
    node.ptrl = 0
    node.type = len(llvm_type)-1
    declared_structs[node.tkname()] = node

def parse_vardecl(node):
    node.token = tokens.consume()
    if not tokenizable(node.tkname()):
        parser_error(node.token, "Invalid variable name")
    exists = add_usr_var(node)
    if exists:
        node.kind = kind.VARREF
    debug("[VARDECL]:", node.tkname())
    if tokens.current()[-1] == "=":
        if not exists:
            tokens.consume()
            node.block = parse_expression(0)
        else:
            op_node = Node()
            op_node.token = tokens.consume()
            op_node.kind = kind.OPERAND
            op_node.children.append(node)
            op_node.children.append(parse_expression(0))
            node = op_node
    return node
    # tokens.expect(";")

def parse_varref(node):
    if node.tkname() in current_namespace:
        namespace = current_namespace
    elif node.tkname() in global_vars:
        namespace = global_vars
    else: 
        parser_error(node.token, "'&t' is undeclared")
    
    var_info = namespace[node.tkname()]
    debug("[VARREF]:", node.tkname())
    node.type, node.ptrl = var_info.type, var_info.ptrl
    node.block = parse_incdec()

included_files = []
def parse_inclusion(node) -> list[Node]:
    global tokens, parse_indentation
    opener = tokens.consume()

    is_local = 1
    if opener[-1] not in ("{","("):
        parser_error(opener, "wrong include opener, must use:\n\t- '(' for local files\n\t- '{' for compiler directory files")
    elif opener[-1] == "{":
        is_local = 0
    
    filepath_tk = tokens.consume()

    if not represents_string(filepath_tk[-1]):
        parser_error(filepath_tk, "the file name has to be a string")
    
    filepath_rel = Path(filepath_tk[-1][1:-1])
    if is_local:
        filepath = cwd.joinpath(filepath_rel).__str__()
    else:
        filepath = libs.joinpath(filepath_rel).__str__()
    
    if filepath in included_files:
        parser_error(filepath_tk, "double inclusion, non stopping error, the first inclusion is the only one used", 0)
        node.kind = kind.NULL
    else:
        included_files.append(filepath)
        og_tokens = tokens
        try:
            with open(filepath, "r") as fp:
                contents = fp.read()
        except Exception as e:
            parser_error(filepath_tk, f"failed to open file &t while trying to include - {e}")
        
        debug("READING SRCODE from:", contents)

        parsed_tokens = get_purified_tokens(contents, filepath)
        debug("[PARSEDTKS]:", [tk[-1] for tk in parsed_tokens])
        
        tokens = Manager(parsed_tokens)
        og_pi = parse_indentation
        parse_indentation = 0

        while tokens.more():
            if (pnode:=parse_primary()).kind != kind.NULL:
                node.children.append(pnode)

        parse_indentation = og_pi
        tokens = og_tokens
    
    if opener[-1] == "(":
        tokens.expect(")")
    else:
        tokens.expect("}")
    return node
    

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
        node.type, node.ptrl = sw_type.CHAR, 1
        if escaped_string not in declared_strings:
            declared_strings.append(llvm_escape(node.tkname()))
        node.val = declared_strings.index(escaped_string)
        
    elif token[-1] in human_unarys:
        debug("[UNARYFOUND]")
        node.kind = kind.UNARY
        node.block = parse_primary()
        
    elif token[-1] == "(":
        node.kind = kind.EXPRESSION
        node.children.append(parse_expression(0))
        tokens.expect(")")
    
    elif token[-1] == "{":
        node.kind = kind.BLOCK
        tokens.goback()
        node = parse_block()
    
    elif token[-1] == "&":
        node.kind = kind.GETPTR
        node.block = parse_primary()
        node.type = node.block.type
        node.ptrl = node.block.ptrl

    elif token[-1] == "*":
        node.kind = kind.REFPTR
        node.block = parse_primary()
        node.type = node.block.type
        node.ptrl = node.block.ptrl

    elif token[-1] == "func":
        # assume_global(token)
        node.kind = kind.FUNCDECL
        parse_funcdecl(node)

    elif token[-1] == "extern":
        # assume_global(token)
        node.kind = kind.EXTERN
        parse_extern(node)
    
    elif token[-1] == "sizeof":
        node.kind = kind.SIZEOF
        tokens.expect("(")
        node.block = parse_expression(0)
        tokens.expect(")")

    elif token[-1] == "struct":
        # assume_global(token)
        node.kind = kind.STRUCT
        parse_struct(node)

    elif token[-1] == "return":
        # forbid_global(token)
        node.kind = kind.RET
        if tokens.current()[-1] != ";":
            debug("[RETURN]: has children")
            node.children.append(parse_expression(0))
        else:
            debug("[RETURN]: no children")

    elif token[-1] == "++":
        node.kind = kind.INC
        node.block = parse_expression(0)
        # node.type, node.ptrl = node.block.type, node.block.ptrl
    
    elif token[-1] == "--":
        node.kind = kind.DEC
        node.block = parse_expression(0)
        # node.type, node.ptrl = node.block.type, node.block.ptrl

    elif token[-1] == "if":
        # forbid_global(token)
        node.kind = kind.IF
        node.block = parse_primary()
        node.children.append(parse_primary())
        if tokens.current()[-1] == "else":
            tokens.inc()
            node.children.append(parse_primary())
        # tokens.assume(";")

    elif token[-1] == "while":
        # forbid_global(token)
        node.kind = kind.WHILE
        node.children.append(parse_primary())
        node.block = parse_primary()

    elif token[-1] == "macro":
        if parse_indentation:
            parser_error(token, "macro statements can only be made at a global level")
        node = parse_macro_decl()
        node.kind = kind.MACRODECL
        
    elif token[-1] == "include":
        node.kind = kind.BLOCK
        node = parse_inclusion(node)

    elif token[-1] == "cast":
        node.kind = kind.CAST
        node.children.append(parse_expression(0))
        tokens.expect("as")
        type_node = Node()
        type_node.token = tokens.current()
        type_node.type, type_node.ptrl = parse_type(0)
        node.children.append(type_node)

    elif token[-1] in human_type:
        node.kind = kind.VARDECL
        tokens.goback() # no one will see this...
        node.type, node.ptrl = parse_type(0)
        if uisalnum(tokens.current()[-1]):
            node = parse_vardecl(node)
        else:
            node.kind = kind.TYPE

    elif token[-1] in current_namespace or token[-1] in global_vars:
        node.kind = kind.VARREF
        parse_varref(node)

    elif token[-1] in declared_funcs:
        node.kind = kind.FUNCCALL
        parse_funcall(node)

    elif token[-1] in macro_tokens:
        node = parse_macro_call()
        node.kind = kind.BLOCK
        node.token = token

    elif tokenizable(token[-1]):
        if parse_indentation:
            node.kind = kind.WORD
            if tokens.current()[-1] == "(":
                parser_error(token, "Undeclared macro or function cannot be called")
            node.block = parse_incdec()
        else:
            parser_error(token, "Unknown instruction '&t'")

    else:
        parser_error(token, "Unexpected symbol '&t'")

    return node

def parse_expression(importance): # <- wanted to write priority
    global parse_indentation; parse_indentation += 1
    node = parse_primary()
    debug("parsing primary from expression parser:", node.tkname(), "current", tokens.current()[-1], "current importance", get_importance(tokens.current()), "importance", importance)
    while tokens.more() and get_importance(tokens.current()) > importance and tokens.current()[-1] in human_operands or node.kind == kind.VARREF and tokens.current()[-1] == ".":
        debug("[parsing tk]", tokens.current())
        op_token = tokens.consume()
        op_node = Node()
        op_node.token = op_token
        op_node.kind = kind.OPERAND
        op_node.children.append(node)
        op_node.type, op_node.ptrl = node.type, node.ptrl
        if op_token[-1] == "[":
            right_node = parse_expression(0)
            tokens.expect("]")
        else:
            right_node = parse_expression(get_importance(op_token))
        op_node.children.append(right_node)
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

def type_cmp(type1, ptrl1, type2, ptrl2):
    if ptrl1 and ptrl2:
        return 1
    else:
        return type1, ptrl1 == type2, ptrl2

def cast(src: str, src_type: int, src_ptrl: int, dest_type: int, dest_ptrl: int, level: int) -> tuple[str, int, int]:
    typecmp = bool(src_ptrl) - bool(dest_ptrl) # > 0 
    isptr = src_ptrl or dest_ptrl
    bothp = src_ptrl and dest_ptrl
    if (src_type, src_ptrl) == (dest_type, dest_ptrl):
        debug("Not casting, cuz same")
        return src, dest_type, dest_ptrl
    if DEBUGGING:
            out_writeln(f"; Casting from {rlt(src_type, src_ptrl)} to {rlt(dest_type, dest_ptrl)}", level)
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
    return f"%{iota(-1)}", dest_type, dest_ptrl #iota -1 : casted val

def incdec(value: str, destination: str, incdec_kind: int, node: Node, level: int) -> str:
    out_writeln(f"; Invoked afterref {human_kind[incdec_kind]}", level)
    if incdec_kind == kind.INC:
        out_writeln(f"%{iota()} = add {rlt(node.type, node.ptrl)} {value}, 1", level)
        out_writeln(f"store {rlt(node.type, node.ptrl)} %{iota(-1)}, ptr {destination}", level)

    if incdec_kind == kind.DEC:
        out_writeln(f"%{iota()} = sub {rlt(node.type, node.ptrl)} {value}, 1", level)
        out_writeln(f"store {rlt(node.type, node.ptrl)} %{iota(-1)}, ptr {destination}", level)
    return f"%{iota(-1)}"

def compile_debug(func):
    def wrapper(*children, **kwchildren):
        ret = func(*children, *kwchildren)
        if DEBUGGING:
            out_writeln(f"; compiled node with kind: {human_kind[children[0].kind]} :: {rlt(children[0].type, children[0].ptrl)} :: name {children[0].tkname()}", children[1])
        return ret
    return wrapper

@compile_debug
def compile_node(node, level, assignable = 0):
    check_global(node, level)
    nlevel = level+1
    arg_names = []
    debug("[COMPILING]:", human_kind[node.kind], "||",)

    if len(node.children) > 1:
        dest_node = node.children[0]
        src_node = node.children[1]

    match node.kind:
        case kind.EXPRESSION:
            for arg in node.children:
                arg_names.append(compile_node(arg, level, assignable))
                node.type, node.ptrl = arg.type, arg.ptrl
            return f"{arg_names[-1]}"

        case kind.RET:
            for arg in node.children:
                argn = compile_node(arg, level)
            if len(node.children):
                out_writeln(f"ret {rlt(node.children[-1].type, node.children[-1].ptrl)} {argn}", level)
            else:
                out_writeln("ret void", level)
        
        case kind.BLOCK:
            for arg in node.children:
                ret = compile_node(arg, level)
                node.type, node.ptrl = arg.type, arg.ptrl
                if arg.kind == kind.RET:
                    debug("[BLOCK]->[RETURNING] -- kind = NULL")
                    node.kind = kind.RET
                    break
            return ret

        case kind.SIZEOF:
            compile_node(node.block, level)
            node.type, node.ptrl = node.block.type, node.block.ptrl
            out_writeln(f"%{iota()} = getelementptr {rlt(node.type, node.ptrl)}, {rlt(node.type, node.ptrl+1)} null, i32 1", level)
            out_writeln(f"%{iota()} = ptrtoint {rlt(node.type, node.ptrl+1)} %{iota(-1)-1} to i64", level)
            node.type = sw_type.INT
            node.ptrl = 0
            return f"%{iota(-1)}"

        case kind.STR_LIT:
            node.type = sw_type.CHAR
            node.ptrl = 1
            return f"@str.{node.val}"

        case kind.NUM_LIT:
            node.type = sw_type.INT
            node.ptrl = 0
            return f"{node.tkname()}"
        
        case kind.TYPE:
            ...

        case kind.UNARY:
            result = compile_node(node.block, level)
            if node.tkname() == "-":
                node.type, node.ptrl = node.block.type, node.block.ptrl
                if node.block.kind == kind.NUM_LIT:
                    node.kind = kind.NUM_LIT
                    result = "-"+result
                    return result
                else:
                    out_writeln(f"%{iota()} = sub {rlt(node.block.type, node.block.ptrl)} 0, {result}", level)
            elif node.tkname() == "!":
                result = cast(result, node.block.type, node.block.ptrl, sw_type.INT, 0, level)[0]
                out_writeln(f"%{iota()} = icmp eq i64 {result}, 0", level)
                node.type, node.ptrl = sw_type.BOOL, 0
                return f"%{iota(-1)}"
            else:
                return result

        case kind.CAST:
            dest = compile_node(dest_node, level)
            ret_val = cast(dest, dest_node.type, dest_node.ptrl, src_node.type, src_node.ptrl, level)[0]
            node.type, node.ptrl = src_node.type, src_node.ptrl
            return ret_val

        case kind.VARDECL:
            if level:
                out_writeln(f"%{node.tkname()} = alloca {rlt(node.type, node.ptrl)}", level)
                if node.block:
                    to_assign = compile_node(node.block, level)
                    if node.block.ptrl and node.ptrl and node.type == sw_type.CHAR:
                        out_writeln(f"store ptr {to_assign}, ptr %{node.tkname()}", level)
                    
                    elif node.block.kind != kind.NUM_LIT and (node.type, node.ptrl) != (node.block.type, node.block.ptrl):
                        casted = cast(to_assign, node.block.type, node.block.ptrl, node.type, node.ptrl, level)[0]
                        out_writeln(f"store {rlt(node.type, node.ptrl)} {casted}, ptr %{node.tkname()}", level)
                        # compiler_error(node, f"Types don't match in variable declaration '{hlt(node.type, node.ptrl)}' != '{hlt(node.block.type, node.block.ptrl)}'")
                    
                    elif node.block.kind == kind.NUM_LIT:
                        out_writeln(f"store {rlt(node.type, 0)} {to_assign}, ptr %{node.tkname()}", level)
                    
                    else:
                        out_writeln(f"store {rlt(node.type, node.ptrl)} {to_assign}, ptr %{node.tkname()}", level)
                    # out_writeln(f"store {rlt(node.type, node.ptrl)} {to_assign}, ptr %{node.tkname()}", level)
            else:
                argn = compile_node(node.block, level)
                if node.ptrl:
                    out_writeln(f"@{node.tkname()} = global {rlt(node.type, node.ptrl)} null", level)
                else:
                    out_writeln(f"@{node.tkname()} = global {rlt(node.type, node.ptrl)} {argn}", level)

        case kind.VARREF:
            if assignable:
                # node.ptrl += 1
                if node.tkname() in global_vars:
                    return f"@{node.tkname()}"
                else:
                    return f"%{node.tkname()}"
            else:
                if node.tkname() in global_vars:
                    out_writeln(f"%{iota()} = load {rlt(node.type, node.ptrl)}, ptr @{node.tkname()}", level)
                else:
                    out_writeln(f"%{iota()} = load {rlt(node.type, node.ptrl)}, ptr %{node.tkname()}", level)

                ret_val = f"%{iota(-1)}"
                
                if node.block:
                    if node.tkname() in global_vars:
                        incdec(f"%{iota(-1)}", f"@{node.tkname()}", node.block.kind, node, level)
                    else:
                        incdec(f"%{iota(-1)}", f"%{node.tkname()}", node.block.kind, node, level)
                
                return ret_val
        
        case kind.INC:
            dest = compile_node(node.block, level, 1)
            node.type, node.ptrl = node.block.type, node.block.ptrl-1
            debug("[INCR KIND]", human_kind[node.block.kind])
            out_writeln(f"%{iota()} = load {rlt(node.block.type, node.block.ptrl-1)}, ptr {dest}", level)
            out_writeln(f"%{iota()} = add {rlt(node.block.type, node.block.ptrl-1)} %{iota(-1)-1}, 1", level)
            out_writeln(f"store {rlt(node.block.type, node.block.ptrl-1)} %{iota(-1)}, ptr {dest}", level)
            return f"%{iota(-1)}"

        case kind.DEC:
            dest = compile_node(node.block, level, 1)
            node.type, node.ptrl = node.block.type, node.block.ptrl-1
            debug("[DECR KIND]", human_kind[node.block.kind])
            out_writeln(f"%{iota()} = load {rlt(node.block.type, node.block.ptrl-1)}, ptr {dest}", level)
            out_writeln(f"%{iota()} = sub {rlt(node.block.type, node.block.ptrl-1)} %{iota(-1)-1}, 1", level)
            out_writeln(f"store {rlt(node.block.type, node.block.ptrl-1)} %{iota(-1)}, ptr {dest}", level)
            return f"%{iota(-1)}"

        case kind.OPERAND:
            if node.tkname() == "=":
                dest = compile_node(dest_node, level, 1)
                debug(f"[OPERAND]: source node is of kind {human_kind[src_node.kind]}")
                src = compile_node(src_node, level)
                if src_node.ptrl and dest_node.ptrl and dest_node.type == sw_type.CHAR:
                    out_writeln(f"store ptr {src}, ptr {dest}", level)
                elif src_node.kind == kind.NUM_LIT:
                    out_writeln(f"store {rlt(dest_node.type, dest_node.ptrl)} {src}, ptr {dest}", level)
                elif not type_cmp(src_node.type, src_node.ptrl, dest_node.type, dest_node.ptrl):
                    compiler_error(node, f"Types don't match in assignment '{hlt(dest_node.type, dest_node.ptrl)}' != '{hlt(src_node.type, src_node.ptrl)}'")
                else:
                    out_writeln(f"store {rlt(dest_node.type, dest_node.ptrl)} {src}, ptr {dest}", level) ## edited
                if src_node.block:
                    incdec(node, src_node.kind, level)
                return src
            
            elif node.tkname() == "[":
                dest = compile_node(dest_node, level) # assignable
                src = compile_node(src_node, level)
                if not dest_node.ptrl:
                    compiler_error(dest_node, "Can only index into pointers")
                out_writeln(f"%{iota()} = getelementptr {rlt(dest_node.type, dest_node.ptrl-1)}, ptr {dest}, i64 {src}", level)
                if not assignable:
                    out_writeln(f"%{iota()} = load {rlt(dest_node.type, dest_node.ptrl-1)}, ptr %{iota(-1)-1}", level)
                    node.type, node.ptrl = dest_node.type, dest_node.ptrl-1
                else:
                    node.type, node.ptrl = dest_node.type, dest_node.ptrl-1
                return f"%{iota(-1)}"
            
            elif node.tkname() == ".":
                dest = f"{compile_node(dest_node, level, 1)}"
                if dest_node.ptrl > 1:
                    compiler_error(node, "Cannot treat a pointer as a structure.")
                struct_node = declared_structs[hlt(dest_node.type, 0)]
                field_id = struct_node.find_by_name(src_node.tkname(), src_node)
                field_node = struct_node.children[field_id]
                debug("[FIELD TYPE]:", hlt(field_node.type, field_node.ptrl))
                out_writeln(f"%{iota()} = getelementptr {rlt(struct_node.type, struct_node.ptrl)}, ptr {dest}, i32 0 ,i32 {field_id}", level)
                if assignable:
                    node.type, node.ptrl = field_node.type, field_node.ptrl
                else:
                    node.type, node.ptrl = field_node.type, field_node.ptrl
                    out_writeln(f"%{iota()} = load {rlt(field_node.type, field_node.ptrl)}, ptr %{iota(-1)-1}", level)
                ret_val = f"%{iota(-1)}"
                if src_node.block:
                    debug("[FIELD SCR NODE]: compiling incdec", src_node.block)
                    incdec(ret_val, f"%{iota(-1)-1}", src_node.block.kind, node, level)
                debug("[NODE TYPE]:", hlt(node.type, node.ptrl))
                return ret_val
                
            else:
                for idx, arg in enumerate(node.children):
                    arg_names.append(compile_node(arg, level))
                    # debug("types for node:", node.tkname(), hlt(node.type, node.ptrl), hlt(arg.type, arg.ptrl))
                    if not idx:
                        node.ptrl, node.type = arg.ptrl, arg.type # operand type is type of the first operand
                
                if (src_node.type, src_node.ptrl) != (node.type, node.ptrl):
                    if src_node.ptrl or node.ptrl:
                        if node.tkname() in ("+","-","*","/","%"):
                            compiler_error(node, "cannot permorm arithmetic operations on pointers, please cast to int, then back to pointers")
                        else:
                            compiler_error(node, "cannot permorm logic operations on pointers, please cast to int, then back to pointers")
                    casted_src = cast(arg_names[1], src_node.type, src_node.ptrl, node.type, node.ptrl, level)[0]
                else:
                    casted_src = arg_names[1]

                match node.tkname():
                    case "+":
                        out_writeln(f"%{iota()} = add {rlt(node.type, node.ptrl)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "-":
                        out_writeln(f"%{iota()} = sub {rlt(node.type, node.ptrl)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "*":
                        out_writeln(f"%{iota()} = mul {rlt(node.type, node.ptrl)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "/":
                        out_writeln(f"%{iota()} = sdiv {rlt(node.type, node.ptrl)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "%":
                        out_writeln(f"%{iota()} = srem {rlt(node.type, node.ptrl)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"

                    case ">":
                        out_writeln(f"%{iota()} = icmp sgt {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    case "<":
                        out_writeln(f"%{iota()} = icmp slt {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    case ">=":
                        out_writeln(f"%{iota()} = icmp sge {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    case "<=":
                        out_writeln(f"%{iota()} = icmp sle {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    case "==":
                        out_writeln(f"%{iota()} = icmp eq {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                    case "!=":
                        out_writeln(f"%{iota()} = icmp ne {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)

                    case "&":
                        out_writeln(f"%{iota()} = and {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "|":
                        out_writeln(f"%{iota()} = or {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "^":
                        out_writeln(f"%{iota()} = xor {rlt(node.type, node.ptrl)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"

                    case "&&":
                        lhs = cast(arg_names[0], node.children[0].type, node.children[0].ptrl, sw_type.BOOL, 0, nlevel)[0]
                        rhs = cast(arg_names[1], node.children[1].type, node.children[1].ptrl, sw_type.BOOL, 0, nlevel)[0]
                    
                        lbl_end = f"and_end_{iota()}"
                        lbl_rhs = f"and_rhs_{iota(-1)}"
                        rhs_val = f"%{iota()}"
                        result_var = f"%{iota()}"

                        out_writeln(f"br i1 {lhs}, label %{lbl_rhs}, label %{lbl_end}", level)

                        out_writeln(f"{lbl_rhs}:", level)
                        out_writeln(f"{rhs_val} = icmp ne i1 {rhs}, 0", level)
                        out_writeln(f"br label %{lbl_end}", level)

                        out_writeln(f"{lbl_end}:", level)
                        out_writeln(f"{result_var} = select i1 {lhs}, i1 {rhs_val}, i1 0", level)

                        node.type, node.ptrl = sw_type.BOOL, 0
                        return result_var


                    case "||":
                        lhs = cast(arg_names[0], node.children[0].type, node.children[0].ptrl, sw_type.BOOL, 0, nlevel)[0]
                        rhs = cast(arg_names[1], node.children[1].type, node.children[1].ptrl, sw_type.BOOL, 0, nlevel)[0]

                        lbl_end = f"or_end_{iota()}"
                        lbl_rhs = f"or_rhs_{iota(-1)}"
                        rhs_val = f"%{iota()}"
                        result_var = f"%{iota()}"

                        out_writeln(f"br i1 {lhs}, label %{lbl_end}, label %{lbl_rhs}", level)

                        out_writeln(f"{lbl_rhs}:", level)
                        out_writeln(f"{rhs_val} = icmp ne i1 {rhs}, 0", level)
                        out_writeln(f"br label %{lbl_end}", level)

                        out_writeln(f"{lbl_end}:", level)
                        out_writeln(f"{result_var} = select i1 {lhs}, i1 1, i1 {rhs_val}", level)

                        node.type, node.ptrl = sw_type.BOOL, 0
                        return result_var

                if node.tkname() in [">", "<", ">=", "<=", "==", "!="]:
                    node.type, node.ptrl = sw_type.BOOL, 0
                    return f"%{iota(-1)}"


        case kind.GETPTR:
            name = compile_node(node.block, level, 1)
            node.kind = node.block.kind
            node.ptrl += 1
            return f"{name}"

        case kind.REFPTR:
            dest = compile_node(node.block, level)
            if not node.block.ptrl:
                compiler_error(node, "Only pointers can be dereferenced")
            out_writeln(f"%{iota()} = getelementptr {rlt(node.block.type, node.block.ptrl-1)}, ptr {dest}, i64 0", level)
            if not assignable:
                out_writeln(f"%{iota()} = load {rlt(node.block.type, node.block.ptrl-1)}, ptr %{iota(-1)-1}", level)
                node.type, node.ptrl = node.block.type, node.block.ptrl-1
            else:
                node.type, node.ptrl = node.block.type, node.block.ptrl-1
            return f"%{iota(-1)}"
           
        case kind.EXTERN:
            out_write(f"declare {rlt(node.type, node.ptrl)} @{node.tkname()}(", level)
            for idx, arg in enumerate(node.children):
                if idx:
                    out_write(", ", 0)
                out_write(rlt(arg.type, arg.ptrl), 0)
            out_writeln(")\n", 0)
        
        case kind.FUNCCALL:
            arg_types = []
            if node.tkname() in ("va_start", "va_end"):
                to_call = "llvm."+node.tkname()
            else:
                to_call = node.tkname()
            funcinfo = declared_funcs[node.tkname()]

            var_length = 0
            if len(funcinfo.children):
                if funcinfo.children[-1].type == sw_type.ANY:
                    var_length = 1
                
            if not var_length and len(funcinfo.children) != len(node.children):
                compiler_error(node, f"The number of arguments passed to '&t' must be {len(funcinfo.children)}")
            
            for idx, arg in enumerate(node.children):
                arg_names.append(compile_node(arg, level))

                if var_length:
                    if arg.type == -1:
                        arg.type, arg.ptrl = funcinfo.children[idx].type, funcinfo.children[idx].ptrl

                    elif idx < len(funcinfo.children) and not type_cmp(arg.type, arg.ptrl, funcinfo.children[idx].type, funcinfo.children[idx].ptrl):
                        compiler_error(arg, f"Argument types don't match with function declaration: {hlt(funcinfo.children[idx].type, funcinfo.children[idx].ptrl)} != {hlt(arg.type, arg.ptrl)}")
            
            if (funcinfo.type, funcinfo.ptrl) == (sw_type.VOID, 0):
                out_write(f"call void @{to_call}(", level); iota()
            else:
                out_write(f"%{iota()} = call {rlt(funcinfo.type, funcinfo.ptrl)} @{node.tkname()}(", level)
            for idx, arg in enumerate(arg_names):
                if idx:
                    out_write(", ", 0)
                out_write(f"{rlt(node.children[idx].type, node.children[idx].ptrl)} {arg}", 0)
            out_writeln(")", 0)
        
        case kind.FUNCDECL:
            global iota_counter
            iota_counter = -1
            out_write(f"define {rlt(node.type, node.ptrl)} @{node.tkname()}(", level)
            for idx, arg in enumerate(node.children):
                if idx:
                    out_write(", ", 0)
                if arg.type != sw_type.ANY:
                    out_write(f"{rlt(arg.type, arg.ptrl)} %{iota()}", 0)
                else:
                    out_write(f"...", 0)
            out_writeln(") {", 0)
            iota_counter = -1
            for arg in node.children:
                if arg.type != sw_type.ANY:
                    out_writeln(f"%{arg.tkname()} = alloca {rlt(arg.type, arg.ptrl)}", nlevel)
                    out_writeln(f"store {rlt(arg.type, arg.ptrl)} %{iota()}, ptr %{arg.tkname()}", nlevel)
            iota()
            compile_node(node.block, nlevel)
            out_writeln("}\n", 0)
        
        case kind.STRUCT:
            out_write(f"%struct.{node.tkname()} = type {{", level)
            for idx, arg in enumerate(node.children):
                if idx:
                    out_write(", ", level)
                out_write(f"{rlt(arg.type, arg.ptrl)}", level)
            out_writeln("}", level)

        case kind.IF:
            compiled_node = compile_node(node.block, nlevel)

            then_node = node.children[0]
            branch_id = iota()
            has_else = len(node.children) > 1

            condition = cast(compiled_node, node.block.type, node.block.ptrl, sw_type.BOOL, 0, level)[0]
            
            if has_else:
                else_node = node.children[1]
                out_writeln(f"br i1 {condition}, label %then.{branch_id}, label %else.{branch_id}", level)
            else:
                out_writeln(f"br i1 {condition}, label %then.{branch_id}, label %done.{branch_id}", level)
            out_writeln(f"then.{branch_id}:", level)
            compile_node(then_node, nlevel)
            if has_else:
                if then_node.kind != kind.RET:
                    out_writeln(f"br label %done.{branch_id}", nlevel)
                out_writeln(f"else.{branch_id}:", level)
                compile_node(else_node, nlevel)
                then_node = else_node # this is so that even when this branch is not ran, the code can continue with the then_node
            debug("[BLOCK]->[RETURNED] -- kind =", human_kind[then_node.kind])
            if then_node.kind != kind.RET:
                out_writeln(f"br label %done.{branch_id}", nlevel)
            out_writeln(f"done.{branch_id}:", level)

        case kind.WHILE:
            branch_id = iota()

            out_writeln(f"br label %cond.{branch_id}", level)
            out_writeln(f"cond.{branch_id}:", level)
            compiled_node = compile_node(node.children[0], nlevel)
            condition = cast(compiled_node, node.children[0].type, node.children[0].ptrl, sw_type.BOOL, 0, nlevel)[0]
            out_writeln(f"br i1 {condition}, label %loop.{branch_id}, label %done.{branch_id}", nlevel)
            out_writeln(f"loop.{branch_id}:", level)
            compile_node(node.block, nlevel)
            out_writeln(f"br label %cond.{branch_id}", nlevel)
            out_writeln(f"done.{branch_id}:", level)
            
        # purposelly: uncompilables - not compilable
        case kind.MACRODECL:
            if DEBUGGING:
                out_writeln("; '{node.tkname()}' macro declared here", level)

        # case kind.NULL: # null nodes should not make it to the compilation stage
        #     ...

        case _:
            compiler_error(node, "Unexpected unqualified token '&t' cannot be compiled")
    return f"%{iota(-1)}"

def compile_nodes(nodes):
    iota(1)
    for node in nodes:
        compile_node(node, 0)

iota(1)
for string in declared_strings:
    out_writeln(f"@str.{iota()-1} = global [{llvm_len(string)-1} x i8] c\"{string[1:-1]}\\00\"", 0)
out_writeln("", 0)

for node in nodes:
    print_node(node)
    if DEBUGGING:
        print()

compile_nodes(nodes)

out.close()

debug(declared_structs, "\n", human_type, "\n", [(x.type, x.ptrl) for key, x in declared_structs.items()])

os.system(f"{args.backend} {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module {args.bflags}")
if DEBUGGING:
    os.system(f"del {OUTFILE_PATH}")
