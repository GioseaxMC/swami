import os
from pathlib import Path
from dataclasses import dataclass
from sys import *
from colorama import Fore as f
from pprint import pp
from copy import copy
argc = len(argv)
import argparse


cwd = Path(os.getcwd())
libs = Path(os.path.realpath(__file__)).parent / "libs"

parser = argparse.ArgumentParser(description="Swami compiler:\n\tusage: <python> swami.py main.sw -o main")

parser.add_argument('-backend', default="clang", help="the language backend to use to compile llvm (default clang)")
parser.add_argument('-d', action='store_true', help="Enable # debug mode")

parser.add_argument('sourcecode', help="The swami file")

parser.add_argument('-o', help="The output file for both the .ll file and the executable", required=True)
parser.add_argument('-emit-llvm', action='store_true', help="Emit the generated llvm ir")
parser.add_argument('-b', help="Custom flags directly passed to the backend", default="")

import struct
word_bytes = struct.calcsize("P")
parser.add_argument('-word-size', help="The word size in bytes of the outputted binary", default=word_bytes)
args = parser.parse_args()
word_bytes = int(args.word_size)
print(word_bytes)
word_bits = word_bytes*8

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
error_sum = 0

def debug(*children, **kwchildren) -> None:
    if not DEBUGGING:
        return
    print(rgb_text(75,75,75)+"│ "*(parse_indentation+1)+f.RESET, end="")
    print(*children, **kwchildren)

@dataclass
class sw_type:
    PTR  = iota(1)
    INT  = iota()
    I32  = iota()
    I64  = iota()
    VOID = iota()
    CHAR = iota()
    BOOL  = iota()
    ANY = iota()

human_type = [
    "ptr",
    "int",
    "i32",
    "i64",
    "void",
    "char",
    "bool",
    "<>",
]

llvm_type = [
    "ptr",
    f"i{word_bits}",
    "i32",
    "i64",
    "void",
    "i8",
    "i1",
    "...",
]

sizeof_type = [
    word_bytes,
    word_bytes,
    4,
    8,
    0,
    1,
    1,
    0
]

def rlt(tn):
    if (tn.ptrl or tn.outptrl) and tn.type==sw_type.VOID:
        return "ptr"
    else:
        tpn = f"{llvm_type[tn.type]+"*"*tn.ptrl}"
    for idx, ntn in enumerate(tn.children):
        if not idx:
            tpn += "("
        else:
            tpn += ", "
        tpn += rlt(ntn)
    if len(tn.children):
        tpn+=")"
    tpn += "*"*tn.outptrl
    return tpn


def hlt(tn):
    tpn = f"{"ptr "*tn.ptrl}{human_type[tn.type]}"
    for idx, ntn in enumerate(tn.children):
        if not idx:
            tpn += "("
        else:
            tpn += ", "
        tpn += hlt(ntn)
    if len(tn.children):
        tpn+=")"
    tpn += " ptr"*tn.outptrl
    return tpn

TL = "╭"
HH = "─"
TR = "╮"
VV = "│"
BR = "╯"
BL = "╰"

class WindowPrint:
    def __init__(self, color):
        self.strings = []
        self.height = 0
        self.width = 0
        self.color = color
    
    def print(self, string):
        strs = string.split("\n")
        for string in strs:
            self.strings.append(string)
            width = len(list(filter(lambda x: 0 < ord(x) and ord(x) < 127, string)))
            self.width = max(self.width, width)
            self.height += 1
    
    def flush(self):
        print(self.color+TL + HH*(self.width+2) + TR)
        for string in self.strings:
            print(self.color + VV + " " + f.RESET + string, end="")
            print(" "*(self.width-len(string)) + self.color + " " + VV)
        print(self.color+BL + HH*(self.width+2) + BR + f.RESET)


def parser_error(token, prompt, errno = -1):
    global error_sum; error_sum += abs(errno)
    COLOR = f.MAGENTA
    if errno:
        COLOR = f.RED
    p = WindowPrint(COLOR)
    eprint = p.print
    eprint(get_tk_pos(token)+": "+("ERROR" if errno else "WARNING")+": "+prompt.replace("&t", token[-1]))
    with open(token[0], "r") as fp:
        content = fp.read()
        eprint("\n  "+content.split("\n")[token[1]])
        eprint("  "+" "*token[2]+"^")
        eprint("  "+" "*token[2]+"| here")
    p.flush()
    if errno<0:
        exit(errno)

def compiler_error(node, prompt, errno = -1):
    token = node.token
    parser_error(token, prompt, errno)

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
    "(",
    "@",
    "%",
    "->",
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
    idx = 0
    length = len(line)
    while idx < length:
        c = line[idx]
        if c == '"':
            idx += 1
            while idx < length:
                if line[idx] == '"' and (line[idx - 1] != '\\' or (idx >= 2 and line[idx - 2] == '\\')):
                    return max(1, idx + 1)
                idx += 1
            return -1
        if c == '#':
            return -2
        if c in human_operands and (idx == 0 or line[idx - 1] == ' '):
            if line[idx:idx+2] in human_operands:
                return max(1, idx + 2)
            return max(1, idx + 1)
        if not uisalnum(c):
            return max(1, idx)
        idx += 1
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
            if not len(pr_stack):
                parser_error(tk, "This parentesis was never opened")
            if pr_cmp[pr_stack[-1][-1]] != tk[-1]:
                parser_error(pr_stack[-1], "Invalid parentesis pairing starting from here")
            else:
                pr_stack.pop()
    if len(pr_stack):
        parser_error(pr_stack[-1], "Parentesis was never closed here")
    return p_tokens

class typenode:
    def __init__(self):
        self.token = None
        self.type = -1
        self.ptrl = 0
        self.outptrl = 0
        self.children = []
    
    def from_node(node):
        tn = node.tn.copy()
        for cc in node.children:
            tn.children.append(cc.tn.copy())
        return tn

    def is_callable(self):
        return len(self.children)
    
    def isptr(self):
        return self.ptrl or self.outptrl
    
    def iscomplex(self):
        return self.type > sw_type.ANY

    def get_zero(self):
        return "null" if self.isptr() else "0"
    
    def copy(self):
        new = typenode()
        new.type = self.type
        new.ptrl = self.ptrl
        new.children = self.children.copy()
        return new
    
    def simple(self):
        new = typenode()
        new.type = self.type
        new.ptrl = self.ptrl
        return new

    def __add__(self, n):
        new = typenode()
        new.type = self.type
        new.outptrl = self.outptrl
        new.ptrl = self.ptrl+n
        new.children = self.children
        return new

    def __sub__(self, n):
        new = typenode()
        new.type = self.type
        new.ptrl = self.ptrl-n
        new.outptrl = self.outptrl
        new.children = self.children
        return new

def ftn(t, p):
    tpn = typenode()
    tpn.type = t
    tpn.ptrl = p
    return tpn

class Node:
    def __init__(self):
        self.token: tuple = None
        self.string_val: str = ""
        self.int_val: int = 0
        self.kind: int = -1
        self.children: list[Node] = []
        self.tn: typenode = typenode()
        self.block = None
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
    ...
    # debug("swami.py : usage")
    # debug("    swami [input-file] -o <output-file>")
    # debug("")
    # debug("  - [required argument]")
    # debug("  - <optional argument> defaults to main")
    # debug("")


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
    FUNCREF = iota()

    LINK = iota()
    RESERVE = iota()
    BREAK = iota()

    NULL = iota()

human_kind = [
    "number",
    "string",
    "operation",
    
    "expression",
    "function definition",
    "function call",
    
    "block",
    "extern",
    "return",
    
    "variable declaration",
    "varriable reference",
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
    "type",
    "function reference",

    "parameters",
    "reserve",
    "break",

    "null",
]

func_namespaces: dict[str, dict[str, Node]] = {}
global_vars: dict[str, Node] = {}
macro_tokens: dict[str, list[tuple]] = {}

declared_params: list[str] = []
declared_funcs: dict[str, Node] = {}
declared_strings: list[str] = []
declared_structs: dict = {}
declared_macros: dict[str, Node] = {}

current_namespace = global_vars

macro_call_stack: list[Node] = []
loop_stack: list[Node] = []

def add_usr_var(node, parse_indentation):
    global global_vars, current_namespace
    if parse_indentation:
        # debug("[USINGNAMESPACE]: current_namespace for", node.tkname())
        namespace = current_namespace
    else:
        # debug("[USINGNAMESPACE]: global_vars")
        namespace = global_vars
    exists = 0
    if node.tkname() in namespace:
        exists = 1
    namespace[node.tkname()] = node
   
    return exists

class Manager:
    def __init__(self, items):
        if len(items):
            self.items = items
            self.items.append(
                (
                    items[-1][0],
                    items[-1][1],
                    items[-1][2] + len(items[-1][-1]),
                    "<EOT> -> end of tokens"
                )
            )
        else:
            self.items = [
                (0, 0, 0, "<EOT> -> end of tokens")
            ]
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
tokens = Manager(parsed_tokens)

def get_importance(token):
    tkname = token[-1]
    # lower items means higher importance
    ops = [
        ("=",),
        
        ("|",),
        ("&",),
        ("||",),
        ("&&",),

        ("<",),
        (">",),
        ("<=",),
        (">=",),
        ("==",),
        ("!=",),
        
        ("[",),

        ("+", "-"),
        ("*", "/"),
        ("%",),
        ("(",),

        (".",),
    ]
    for idx, op in enumerate(ops):
        if tkname in op:
            return idx+1
    return 0

def iprint(indent, *children, **kwchildren):
    print("| "*indent, *children, *kwchildren)

def print_node(node, indent = 0):
    nindent = indent+1
    if not DEBUGGING:
        return
    iprint(indent, "name::", node.tkname())
    iprint(indent, "kind::", human_kind[node.kind])
    iprint(indent, "type::", hlt(node.tn))
    for arg in node.children:
        print_node(arg, nindent)
    if node.block:
        iprint(indent, "block: ")
        print_node(node.block, nindent)

def check_global(node, level):
    not_global = kind.IF, kind.WHILE, kind.RET, kind.FUNCCALL
    _global = kind.FUNCDECL, kind.EXTERN, kind.STRUCT
    if level:
        if node.kind in _global:
            compiler_error(node, "instruction can only be used at a global level")
    else:
        if node.kind in not_global:
            compiler_error(node, "instruction cannot be used at a global (and so static) level")

nodes: list[Node] = list()

def funcref_from_word(word: Node):
    if word.tkname() in declared_funcs:
        called = declared_funcs[word.tkname()]
        word.tn = typenode.from_node(called)
        word.tn.outptrl+=1
        word.kind = kind.FUNCREF
        return word
    compiler_error(word, "Cannot call unknown word '&t'")

def sizeof(tn: typenode): # in bytes please
    # debug({(type, ptrl)})
    if tn.isptr():
        return word_bytes
    return sizeof_type[tn.type]

def get_max_size(tn: typenode): # in bytes please
    if tn.isptr():
        return word_bytes
    if tn.type > sw_type.ANY:
        structinfo = declared_structs[hlt(tn)]
        max_size = 0
        for child in structinfo.children:
            max_size = max(max_size, get_max_size(child.tn))
    return sizeof(tn)

def parse():
    global parse_indentation
    parse_indentation = 0
    while tokens.more():
        if (node:=parse_primary()).kind != kind.NULL:
            nodes.append(node)

def parse_incdec():
    node: None | Node = None
    # debug("parsing incdec", tokens.current()[-1])
    if tokens.current()[-1] == "++":
        node = Node()
        node.token = tokens.consume()
        node.kind = kind.INC
    elif tokens.current()[-1] == "--":
        node = Node()
        node.token = tokens.consume()
        node.kind = kind.DEC
    return node

def parse_type_base(ptrl):
    typename = tokens.consume()
    if typename[-1] not in human_type:
        parser_error(typename, "Expected typename but got '&t'")
    rtype = human_type.index(typename[-1])
    if rtype == sw_type.VOID:
        if ptrl:
            rtype = sw_type.CHAR
        return rtype, ptrl
    elif rtype == sw_type.PTR:
        return parse_type_base(ptrl+1)
    else:
        return rtype, ptrl

def parse_type(tn):
    tn.token = tokens.current()
    tn.type, tn.ptrl = parse_type_base(0)
    # debug("[AFTER TPARSE]:", tokens.current()[-1])
    tn.outptrl = 0
    # debug("[]", tokens.current()[-1])
    if tokens.current()[-1] == "(":
        tokens.consume()
        while tokens.current()[-1] != ")":
            ntn = typenode()
            parse_type(ntn)
            tn.children.append(ntn)
            if tokens.current()[-1] != ")":
                tokens.expect(",")
        tokens.expect(")")
        while tokens.current()[-1] == human_type[sw_type.PTR]:
            tokens.consume()
            tn.outptrl += 1

def parse_named_arg(closer):
    node = Node()
    parse_type(node.tn)
    if node.tn.type != sw_type.ANY:
        node.token = tokens.consume()
        if not tokenizable(node.tkname()):
            parser_error(node.token, "Invalid name for argument")
    else:
        node.token = tokens.current()
    # debug("[NAMEDARG]:", node.tkname())
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
    if not tokenizable(node.tkname()):
        parser_error(node.token, "Invalid name for argument")
    # debug("[NAMEDARG]:", node.tkname())
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
    # debug("starting macro tokens parsing from", tokens.current())
    while m_parsing:
        token = tokens.consume()
        tkname = token[-1]
        # debug("[MACRO]: parsing", tkname)
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
        # debug("[MACROARG]: parsing", tkname, "with indentation", m_level)
        if tkname in ("(", "{", "["): # check for macro related bugs
            m_level+=1
        if tkname in (")", "}", "]"):
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
    if body_tokens[0][-1] == "[":
        body_tokens = body_tokens[1:-1]
    return body_tokens

def parse_macro_call():
    global tokens, parse_indentation
    node = Node()
    node.token = tokens.prev()
    macro_call_stack.append(node)
    macro_args = []
    tokens.expect("(")
    while tokens.current()[-1] != ")":
        # debug("macro-token-before:", tokens.current()[-1])
        macro_args.append(parse_macro_args())
        # debug("macro-token-after:", tokens.current()[-1])
        if tokens.current()[-1] != ")":
            tokens.expect(",")
    tokens.expect(")")

    if len(macro_args) != len(declared_macros[node.tkname()].children):
        compiler_error(node, f"Expected {len(declared_macros[node.tkname()].children)} tokens but got {len(macro_args)}")

    current_macro_tks = macro_tokens[node.tkname()].copy() # memcopy or da_copy()
    arg_names = [x.tkname() for x in declared_macros[node.tkname()].children]
    

    for idx, arg in enumerate(current_macro_tks):
        # debug(idx, arg)
        if arg[-1] in arg_names:
            arg_idx = arg_names.index(arg[-1])
            current_macro_tks.pop(idx)
            # debug(macro_args)
            for tki, tk in enumerate(macro_args[arg_idx]):
                # debug("--", idx, tk)
                current_macro_tks.insert(idx+tki, tk)

    og_tokens = tokens

    if DEBUGGING:
        for tk in current_macro_tks:
            ...
            # debug("..", tk)
    
    debug("macro_tokens:", node.tkname())
    idx = 0
    while idx<len(current_macro_tks):
        if current_macro_tks[idx][-1] == "@":
            left = current_macro_tks.pop(idx-1)
            current_macro_tks.pop(idx-1)
            right = current_macro_tks.pop(idx-1)
            left = (*left[::-1], left[-1]+right[-1])
            current_macro_tks.insert(idx-1, left)
        else:
            debug(current_macro_tks[idx])
            idx+=1

    tokens = Manager(current_macro_tks)

    # debug("starting macro manager from:", tokens.current())
    old_pi = parse_indentation
    parse_indentation = -1
    while tokens.more():

        # debug("parsing macro_body:", tokens.current())
        node.children.append(parse_expression(0))
        tokens.expect(";")
        
    parse_indentation = old_pi

    tokens = og_tokens
    macro_call_stack.pop()
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
    parse_type(node.tn)
    if node.tn.is_callable():
        parser_error(node.tn.token, "functions cannot return function type or function pointers, just use 'ptr void'")
    node.token = tokens.consume()
    if not tokenizable(node.tkname()):
        parser_error(node.token, "Invalid function name")
    declared_funcs[node.tkname()] = node
    func_namespaces[node.tkname()] = {}
    current_namespace = func_namespaces[node.tkname()]
    # debug("[FUNCDESC]", node.tkname(), ":", hlt(node.tn))
    tokens.expect("(")
    parse_indentation += 1
    node.children = parse_named_args(")")
    for arg in node.children:
        add_usr_var(arg, parse_indentation)
    parse_indentation -= 1
    node.block = parse_block()
    current_namespace = global_vars

def parse_funcall(node):
    while tokens.current()[-1] != ")":
        node.children.append(parse_expression(0))
        if tokens.current()[-1] != ")":
            tokens.expect(",")
    tokens.expect(")")
    return node    

def parse_funcref(node):
    # debug("[FUNCREF]:", node.tkname())
    called = declared_funcs[node.tkname()]
    node.tn = typenode.from_node(called)
    node.tn.outptrl+=1

def parse_unnamed_arg(closer):
    node = Node()
    parse_type(node.tn)
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
    parse_type(node.tn)
    node.token = tokens.consume()
    if node.tkname() in declared_funcs:
        node.kind = kind.NULL
    # debug("[EXTERN]: name:", node.tkname(), rlt(node.tn))
    declared_funcs[node.tkname()] = node
    tokens.expect("(")
    node.children = parse_unnamed_args(")")
    tokens.expect(")")

def parse_struct(node):
    node.token = tokens.consume()
    # debug(f"[STRUCT]: {node.tkname()}")
    human_type.append(node.tkname())
    llvm_type.append(f"%struct.{node.tkname()}")
    tokens.expect("{")
    node.children = parse_named_args("}")
    size = 0
    max_size = 0
    for nd in node.children:
        y = sizeof(nd.tn)
        max_size = max(max_size, get_max_size(nd.tn))
        size = size + ((y - size%y) % y) + y
    size = size + (max_size - size%max_size) % max_size
    sizeof_type.append(size)
    node.tn.ptrl = 0
    node.tn.type = len(llvm_type)-1
    declared_structs[node.tkname()] = node

def parse_vardecl(node):
    node.token = tokens.consume()
    if not tokenizable(node.tkname()):
        parser_error(node.token, "Invalid variable name")
    exists = add_usr_var(node, parse_indentation)
    if exists:
        node.kind = kind.VARREF
    # debug("[VARDECL]:", node.tkname())
    if tokens.current()[-1] == "=":
        if not exists:
            tokens.consume()
            # debug("[PARSING DECLASS]:", tokens.current()[-1])
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
    debug(node.tkname())
    if node.tkname() in current_namespace:
        namespace = current_namespace
    elif node.tkname() in global_vars:
        namespace = global_vars
    else: 
        parser_error(node.token, "'&t' is undeclared") # this should be unreachable but still
    
    var_info = namespace[node.tkname()]
    # debug("[VARREF]:", node.tkname())
    node.tn = var_info.tn.copy()
    node.block = parse_incdec()

included_files: list[str] = []
def parse_inclusion(node) -> Node:
    global tokens, parse_indentation
    opener = tokens.consume()

    is_local = 1
    if opener[-1] not in ("{","("):
        parser_error(opener, "wrong include opener, must use:\n\t- '(' for local files\n\t- '{' for compiler directory files")
    elif opener[-1] == "{":
        is_local = 0
    closer = pr_cmp[opener[-1]]
    if tokens.current()[-1] == closer:
        parser_error(opener, "Expected at least a file to include")
    while tokens.current()[-1] != closer:
        filepath_tk = tokens.consume()

        if not represents_string(filepath_tk[-1]):
            parser_error(filepath_tk, "the file name has to be a string")
        
        filepath_rel = Path(filepath_tk[-1][1:-1])
        if is_local:
            filepath = cwd.joinpath(filepath_rel).__str__()
        else:
            filepath = libs.joinpath(filepath_rel).__str__()
        
        if filepath in included_files:
            ...
            # parser_error(filepath_tk, "double inclusion, the first inclusion is the only one used", 0)
        
        else:
            included_files.append(filepath)
            og_tokens = tokens
            try:
                with open(filepath, "r") as fp:
                    contents = fp.read()
            except Exception as e:
                parser_error(filepath_tk, f"failed to open file &t while trying to include - {e}")
            
            # debug("READING SRCODE from:", contents)

            parsed_tokens = get_purified_tokens(contents, filepath)
            # debug("[PARSEDTKS]:", [tk[-1] for tk in parsed_tokens])
            
            tokens = Manager(parsed_tokens)
            og_pi = parse_indentation
            parse_indentation = 0

            while tokens.more():
                if (pnode:=parse_primary()).kind != kind.NULL:
                    node.children.append(pnode)

            parse_indentation = og_pi
            tokens = og_tokens
        if tokens.current()[-1] != closer:
            tokens.expect(",")
        
    tokens.expect(closer)
    return node
    

def parse_primary():
    token = tokens.consume()
    # debug(F"[PRIMARY]: '{token[-1]}'")
    node = Node()
    node.token = token

    if token[-1].isnumeric():
        node.kind = kind.NUM_LIT
        
    elif represents_string(token[-1]):
        node.kind = kind.STR_LIT
        escaped_string = llvm_escape(node.tkname())
        node.tn.type, node.tn.ptrl = sw_type.CHAR, 1
        if escaped_string not in declared_strings:
            declared_strings.append(llvm_escape(node.tkname()))
        node.int_val = declared_strings.index(escaped_string)
        
    elif token[-1] in human_unarys:
        # debug("[UNARYFOUND]")
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
        node.block = parse_expression(0)
        node.tn = node.block.tn.copy()

    elif token[-1] == "*":
        node.kind = kind.REFPTR
        node.block = parse_primary()
        node.tn = node.block.tn.copy()

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
            # debug("[RETURN]: has children")
            node.children.append(parse_expression(0))
        else:
            ...
            # debug("[RETURN]: no children")
    
    elif token[-1] == "reserve":
        node.kind = kind.RESERVE
        size_tk = tokens.consume()
        node.string_val = size_tk[-1]
        if not node.string_val.isnumeric():
            parser_error(size_tk, "Expected an integer literal, got '&t'")
        tokens.expect("as")
        node.token = tokens.consume()
        if not tokenizable(node.tkname()):
            parser_error(node.token, "'&t' is not a valid variable name")
        node.tn = ftn(sw_type.CHAR, 1)
        exists = add_usr_var(node, parse_indentation)
        if exists:
            parser_error(node.token, "Redeclaration of variable '&t'")

        
    elif token[-1] == "param":
        node.kind = kind.NULL
        node.string_val = tokens.consume()[-1]
        if node.string_val not in declared_params:
            declared_params.append(node.string_val)
            args.b += f" {node.string_val[1:-1]} "
    
    elif token[-1] == "error":
        msg = tokens.consume()[-1]
        if represents_string(msg):
            msg = msg[1:-1]
        if len(macro_call_stack):
            compiler_error(macro_call_stack.pop(), msg)
        else:
            compiler_error(node, msg)

    elif token[-1] == "++":
        node.kind = kind.INC
        node.block = parse_expression(0)
        # node.tn.type, node.tn.ptrl = node.block.tn.type, node.block.tn.ptrl
    
    elif token[-1] == "--":
        node.kind = kind.DEC
        node.block = parse_expression(0)
        # node.tn.type, node.tn.ptrl = node.block.tn.type, node.block.tn.ptrl

    elif token[-1] == "if":
        # forbid_global(token)
        node.kind = kind.IF
        node.block = parse_expression(0)
        node.children.append(parse_expression(0))
        if tokens.current()[-1] == "else":
            tokens.inc()
            node.children.append(parse_expression(0))
        # tokens.assume(";")

    elif token[-1] == "while":
        # forbid_global(token)
        node.kind = kind.WHILE
        node.children.append(parse_expression(0))
        node.block = parse_expression(0)

    elif token[-1] == "macro":
        # if parse_indentation:
        #     parser_error(token, "macro statements can only be made at a global level")
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
        parse_type(type_node.tn)
        node.children.append(type_node)

    elif token[-1] in human_type:
        node.kind = kind.VARDECL
        tokens.goback() # no one will see this...
        parse_type(node.tn)
        # debug("[AFTER VARDECL]:", tokens.current()[-1])
        if uisalnum(tokens.current()[-1]):
            node = parse_vardecl(node)
        else:
            node.kind = kind.TYPE

    elif token[-1] in current_namespace or token[-1] in global_vars:
        node.kind = kind.VARREF
        parse_varref(node)

    elif token[-1] in declared_funcs:
        node.kind = kind.FUNCREF
        parse_funcref(node)
        

    elif token[-1] in macro_tokens:
        node = parse_macro_call()
        node.kind = kind.BLOCK
        node.token = token

    elif tokenizable(token[-1]):
        if parse_indentation:
            node.kind = kind.WORD
            node.block = parse_incdec()
        else:
            parser_error(token, "Unknown instruction '&t'")

    else:
        parser_error(token, "Unexpected symbol '&t'")

    return node

def parse_expression(importance): # <- wanted to write priority
    global parse_indentation; parse_indentation += 1
    node = parse_primary()
    # debug("parsing primary from expression parser:", node.tkname(), "current", tokens.current()[-1], "current importance", get_importance(tokens.current()), "importance", importance)
    while tokens.more() and get_importance(tokens.current()) > importance and tokens.current()[-1] in human_operands:
        op_token = tokens.consume()
        op_node = Node()
        op_node.token = op_token
        op_node.kind = kind.OPERAND
        op_node.children.append(node)
        op_node.tn.type, op_node.tn.ptrl = node.tn.type, node.tn.ptrl
        if op_token[-1] == "[":
            right_node = parse_expression(0)
            tokens.expect("]")
        elif op_token[-1] == "(":
            right_node = Node()
            right_node.token = tokens.current()
            parse_funcall(right_node)
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

def type_cmp(type1, type2):
    if type1.ptrl and type2.ptrl:
        return 1
    else:
        cond = 1
        for c1, c2 in zip(type1.children, type2.children):
            if not type_cmp(c1, c2):
                return 0
        return (type1.type, type1.ptrl) == (type2.type, type2.ptrl)

def cast(src: str, src_tn: typenode, dest_tn: typenode, level: int) -> tuple[str, typenode]:
    typecmp = src_tn.isptr() - dest_tn.isptr() # > 0 
    isptr = src_tn.isptr() or dest_tn.isptr()
    bothp = src_tn.isptr() and dest_tn.isptr()
    if (src_tn.type, src_tn.ptrl) == (dest_tn.type, dest_tn.ptrl):
        # debug("Not casting, cuz same")
        return src, dest_tn
    if DEBUGGING:
        out_writeln(f"; Casting from {rlt(src_tn)} to {rlt(dest_tn)}", level)
            
    if bothp:
        out_writeln(f"%{iota()} = bitcast {rlt(src_tn)} {src} to {rlt(dest_tn)}", level)

    elif isptr:
        if typecmp > 0:
            if dest_tn.type == sw_type.BOOL:
                out_writeln(f"%{iota()} = ptrtoint {rlt(src_tn)} {src} to i{word_bits}", level)
                out_writeln(f"%{iota()} = icmp ne i{word_bits} %{iota(-1)-1}, 0", level)
            else:
                out_writeln(f"%{iota()} = ptrtoint {rlt(src_tn)} {src} to {rlt(dest_tn)}", level)
        else:
            out_writeln(f"%{iota()} = inttoptr {rlt(src_tn)} {src} to {rlt(dest_tn)}", level)

    else:
        if dest_tn.type == sw_type.BOOL:
            out_writeln(f"%{iota()} = icmp ne {rlt(src_tn)} {src}, 0", level)
        else:
            if sizeof(dest_tn) > sizeof(src_tn):
                out_writeln(f"%{iota()} = zext {rlt(src_tn)} {src} to {rlt(dest_tn)}", level)
            elif sizeof(dest_tn) < sizeof(src_tn):
                out_writeln(f"%{iota()} = trunc {rlt(src_tn)} {src} to {rlt(dest_tn)}", level)
            else:
                out_writeln(f"%{iota()} = bitcast {rlt(src_tn)} {src} to {rlt(dest_tn)}", level)
    return f"%{iota(-1)}", dest_tn

def incdec(value: str, destination: str, incdec_kind: int, node: Node, level: int) -> str:
    out_writeln(f"; Invoked afterref {human_kind[incdec_kind]}", level)
    if incdec_kind == kind.INC:
        out_writeln(f"%{iota()} = add {rlt(node.tn)} {value}, 1", level)
        out_writeln(f"store {rlt(node.tn)} %{iota(-1)}, ptr {destination}", level)

    if incdec_kind == kind.DEC:
        out_writeln(f"%{iota()} = sub {rlt(node.tn)} {value}, 1", level)
        out_writeln(f"store {rlt(node.tn)} %{iota(-1)}, ptr {destination}", level)
    return f"%{iota(-1)}"

def compile_debug(func):
    def wrapper(*children, **kwchildren):
        ret = func(*children, *kwchildren)
        if DEBUGGING:
            out_writeln(f"; compiled node with kind: {human_kind[children[0].kind]} :: {rlt(children[0].tn)} :: name {children[0].tkname()}", children[1])
        return ret
    return wrapper

def both_ints(node1, node2):
    return node1.kind == kind.NUM_LIT and node2.kind == kind.NUM_LIT

@compile_debug
def compile_node(node, level, assignable = 0):
    global iota_counter, current_namespace;

    check_global(node, level)
    nlevel = level+1
    arg_names = []
    # debug("[COMPILING]:", human_kind[node.kind], "||",)

    if len(node.children) > 1:
        dest_node = node.children[0]
        src_node = node.children[1]
    
    if assignable:
        if node.kind in (kind.FUNCCALL,):
            compiler_error(node, f"cannot treat '{human_kind[node.kind]}' as lvalue.")

    match node.kind:
        case kind.EXPRESSION:
            for arg in node.children:
                arg_names.append(compile_node(arg, level, assignable))
                node.tn = arg.tn #.copy()
            return f"{arg_names[-1]}"

        case kind.RET:
            for arg in node.children:
                argn = compile_node(arg, level)
            if len(node.children):
                out_writeln(f"ret {rlt(node.children[-1].tn)} {argn}", level)
            else:
                out_writeln("ret void", level)
        
        case kind.BLOCK:
            ret = ""
            for arg in node.children:
                ret = compile_node(arg, level, assignable)
                node.tn.type, node.tn.ptrl = arg.tn.type, arg.tn.ptrl
                if arg.kind in (kind.RET, kind.BREAK):
                    # debug("[BLOCK]->[RETURNING] -- kind = NULL")
                    node.kind = kind.RET
                    break
            return ret

        case kind.SIZEOF:
            compile_node(node.block, level)
            node.tn.type = sw_type.INT
            node.tn.ptrl = 0
            USE_LEGACY_SIZEOF = 0
            if USE_LEGACY_SIZEOF:
                out_writeln(f"%{iota()} = getelementptr {rlt(node.block.tn)}, {rlt(node.block.tn+1)} null, i32 1", level)
                out_writeln(f"%{iota()} = ptrtoint {rlt(node.tn+1)} %{iota(-1)-1} to i{word_bits}", level)
                return f"%{iota(-1)}"
            else:    
                node.kind = kind.NUM_LIT
                node.token = (*node.token[:3], str(sizeof(node.block.tn)))
                return f"{sizeof(node.block.tn)}"

        case kind.STR_LIT:
            node.tn.type = sw_type.CHAR
            node.tn.ptrl = 1
            return f"@str.{node.int_val}"

        case kind.NUM_LIT:
            node.tn.type = sw_type.INT
            node.tn.ptrl = 0
            return f"{node.tkname()}"
        
        case kind.TYPE:
            ...

        case kind.RESERVE:
            var = iota()
            out_writeln(f"%{var} = alloca [{node.string_val} x i8]", level)
            out_writeln(f"%{node.tkname()} = alloca ptr", level)
            out_writeln(f"store ptr %{var}, ptr %{node.tkname()}", level)
            return f"%{node.tkname()}"

        case kind.UNARY:
            result = compile_node(node.block, level)
            if node.tkname() == "-":
                node.tn = node.block.tn
                if node.block.kind == kind.NUM_LIT:
                    node.kind = kind.NUM_LIT
                    result = "-"+result
                    return result
                else:
                    out_writeln(f"%{iota()} = sub {rlt(node.block.tn)} 0, {result}", level)
            elif node.tkname() == "!":
                # result = cast(result, node.block.tn, ftn(sw_type.INT, 0), level)[0]
                out_writeln(f"%{iota()} = icmp eq {rlt(node.block.tn)} {result}, {node.block.tn.get_zero()}", level)
                node.tn = ftn(sw_type.BOOL, 0)
                return f"%{iota(-1)}"
            else:
                return result

        case kind.CAST:
            dest = compile_node(dest_node, level)
            ret_val = cast(dest, dest_node.tn, src_node.tn, level)[0]
            node.tn = src_node.tn.copy()
            return ret_val

        case kind.VARDECL:
            if level:
                out_writeln(f"%{node.tkname()} = alloca {rlt(node.tn)}", level)
                if node.block:
                    to_assign = compile_node(node.block, level)
                    if node.block.tn.ptrl and node.tn.ptrl and node.tn.type == sw_type.CHAR:
                        out_writeln(f"store ptr {to_assign}, ptr %{node.tkname()}", level)
                    
                    elif node.block.kind != kind.NUM_LIT and (node.tn.type, node.tn.ptrl) != (node.block.tn.type, node.block.tn.ptrl):
                        casted = cast(to_assign, node.block.tn, node.tn, level)[0]
                        out_writeln(f"store {rlt(node.tn)} {casted}, ptr %{node.tkname()}", level)
                        # compiler_error(node, f"Types don't match in variable declaration '{hlt(node.tn.type, node.tn.ptrl)}' != '{hlt(node.block.tn.type, node.block.tn.ptrl)}'")
                    
                    elif node.block.kind == kind.NUM_LIT:
                        out_writeln(f"store {rlt(ftn(node.tn.type, 0))} {to_assign}, ptr %{node.tkname()}", level)
                    
                    else:
                        out_writeln(f"store {rlt(node.tn)} {to_assign}, ptr %{node.tkname()}", level)
                    # out_writeln(f"store {rlt(node.tn.type, node.tn.ptrl)} {to_assign}, ptr %{node.tkname()}", level)
                return f"%{node.tkname()}"
            else:
                if node.block:
                    argn = compile_node(node.block, level)
                    if node.tn.isptr():
                        out_writeln(f"@{node.tkname()} = global {rlt(node.tn)} null", level)
                    elif node.tn.iscomplex():
                        out_writeln(f"@{node.tkname()} = global {rlt(node.tn)} zeroinitializer", level)
                    else:
                        out_writeln(f"@{node.tkname()} = global {rlt(node.tn)} {argn}", level)
                else:
                    out_writeln(f"@{node.tkname()} = global {rlt(node.tn)} zeroinitializer", level)
                return f"@{node.tkname()}"

        case kind.VARREF:
            if assignable:
                # node.tn.ptrl += 1
                if node.tkname() in global_vars:
                    return f"@{node.tkname()}"
                else:
                    return f"%{node.tkname()}"
            else:
                if node.tkname() in global_vars:
                    out_writeln(f"%{iota()} = load {rlt(node.tn)} , {rlt(node.tn+1)}  @{node.tkname()}", level)
                else:
                    out_writeln(f"%{iota()} = load {rlt(node.tn)} , {rlt(node.tn+1)} %{node.tkname()}", level)

                ret_val = f"%{iota(-1)}"
                
                if node.block:
                    if node.tkname() in global_vars:
                        incdec(f"%{iota(-1)}", f"@{node.tkname()}", node.block.kind, node, level)
                    else:
                        incdec(f"%{iota(-1)}", f"%{node.tkname()}", node.block.kind, node, level)
                
                return ret_val
        
        case kind.INC:
            dest = compile_node(node.block, level, 1)
            node.tn.type, node.tn.ptrl = node.block.tn.type, node.block.tn.ptrl-1
            # debug("[INCR KIND]", human_kind[node.block.kind])
            out_writeln(f"%{iota()} = load {rlt(node.block.tn-1)}, ptr {dest}", level)
            out_writeln(f"%{iota()} = add {rlt(node.block.tn-1)} %{iota(-1)-1}, 1", level)
            out_writeln(f"store {rlt(node.block.tn-1)} %{iota(-1)}, ptr {dest}", level)
            return f"%{iota(-1)}"

        case kind.DEC:
            dest = compile_node(node.block, level, 1)
            node.tn.type, node.tn.ptrl = node.block.tn.type, node.block.tn.ptrl-1
            # debug("[DECR KIND]", human_kind[node.block.kind])
            out_writeln(f"%{iota()} = load {rlt(node.block.tn-1)}, ptr {dest}", level)
            out_writeln(f"%{iota()} = sub {rlt(node.block-1)} %{iota(-1)-1}, 1", level)
            out_writeln(f"store {rlt(node.block.tn-1)} %{iota(-1)}, ptr {dest}", level)
            return f"%{iota(-1)}"

        case kind.OPERAND:
            if node.tkname() == "=":
                src = compile_node(src_node, level)
                if dest_node.kind == kind.WORD:
                    if dest_node.tkname() not in current_namespace:
                        dest_node.tn = src_node.tn
                        dest_node.kind = kind.VARDECL
                        add_usr_var(dest_node, level)
                        out_writeln(f"%{dest_node.tkname()} = alloca {rlt(dest_node.tn)}", level)
                        dest = f"%{dest_node.tkname()}"
                    else:
                        dest_node.tn = src_node.tn
                        dest_node.kind = kind.VARREF
                        
                        dest = compile_node(dest_node, level, 1)
                else:
                    dest = compile_node(dest_node, level, 1)
                # debug(f"[OPERAND]: source node is of kind {human_kind[src_node.kind]}")
                if src_node.tn.ptrl and dest_node.tn.ptrl and dest_node.tn.type == sw_type.CHAR:
                    out_writeln(f"store ptr {src}, ptr {dest}", level)
                elif src_node.kind == kind.NUM_LIT:
                    out_writeln(f"store {rlt(dest_node.tn)} {src}, ptr {dest}", level)
                elif not type_cmp(src_node.tn, dest_node.tn):
                    compiler_error(node, f"Types don't match in assignment '{hlt(dest_node.tn)}' != '{hlt(src_node.tn)}'")
                else:
                    out_writeln(f"store {rlt(dest_node.tn)} {src}, ptr {dest}", level) ## edited
                return src
            
            elif node.tkname() == "[":
                dest = compile_node(dest_node, level) # assignable
                src = compile_node(src_node, level)
                if not dest_node.tn.ptrl:
                    compiler_error(dest_node, "Can only index into pointers")
                out_writeln(f"%{iota()} = getelementptr {rlt(dest_node.tn-1)}, ptr {dest}, {rlt(src_node.tn)} {src}", level)
                if not assignable:
                    out_writeln(f"%{iota()} = load {rlt(dest_node.tn-1)}, ptr %{iota(-1)-1}", level)
                    node.tn.type, node.tn.ptrl = dest_node.tn.type, dest_node.tn.ptrl-1
                else:
                    node.tn.type, node.tn.ptrl = dest_node.tn.type, dest_node.tn.ptrl-1
                return f"%{iota(-1)}"
            
            elif node.tkname() == ".":
                do_incdec = 0
                if src_node.block and src_node.block.kind in (kind.INC, kind.DEC):
                    do_incdec = 1
                
                dest = compile_node(dest_node, level, do_incdec or assignable)
                
                while dest_node.tn.ptrl > 0:
                    if not assignable or do_incdec:
                        dest_node.tn.ptrl -= 1
                    # debug("dereference struct")
                    out_writeln(f"; dereferencing sturct", level)
                    out_writeln(f"%{iota()} = load {rlt(dest_node.tn)}, ptr {dest}", level)
                    dest = f"%{iota(-1)}"
                    if assignable or do_incdec:
                        dest_node.tn.ptrl -= 1

                struct_node = declared_structs[hlt(ftn(dest_node.tn.type, 0))]
                field_id = struct_node.find_by_name(src_node.tkname(), src_node)
                field_node = struct_node.children[field_id]
                
                debug(field_node.tkname(), hlt(field_node.tn))

                if assignable or do_incdec:
                    # debug("[FIELD TYPE]:", hlt(field_node.tn))
                    # out_writeln(f"%{iota()} = load {rlt(struct_node.tn.type, struct_node.tn.ptrl)}, ptr {dest}", level)
                    out_writeln(f"%{iota()} = getelementptr {rlt(struct_node.tn)}, ptr {dest}, i32 0 ,i32 {field_id}", level)
                    inc_dest = f"%{iota(-1)}"
                    if not assignable:
                        out_writeln(f"%{iota()} = load {rlt(field_node.tn)}, ptr %{iota(-1)-1}", level)
                else:
                    # out_writeln(f"%{iota()} = load {rlt(struct_node.tn.type, struct_node.tn.ptrl)}, ptr {dest}", level)
                    out_writeln(f"%{iota()} = extractvalue {rlt(struct_node.tn)} {dest}, {field_id}", level)
                node.tn = field_node.tn.copy()

                ret_val = f"%{iota(-1)}"


                if do_incdec:
                    # debug("[FIELD SCR NODE]: compiling incdec", src_node.block)
                    incdec(ret_val, f"%{iota(-1)-1}", src_node.block.kind, node, level)
                # debug("[NODE TYPE]:", hlt(node.tn))
                return ret_val

            elif node.tkname() == "(": # FUNCALL
                if dest_node.kind == kind.WORD:
                    dest_node = funcref_from_word(dest_node)
                dest = compile_node(dest_node, level, 1)
                node.tn = dest_node.tn.simple()
                if dest in ("@va_start", "@va_end", "@va_copy"):
                    to_call = "@llvm."+dest[1:]
                else:
                    to_call = dest
                if dest_node.tkname() in declared_funcs:
                    funcinfo = typenode.from_node(declared_funcs[dest_node.tkname()])
                elif dest_node.tn.is_callable():
                    funcinfo = dest_node.tn
                else:
                    # debug(dest_node)
                    compiler_error(dest_node, "Not a callable")

                var_length = 0
                if len(funcinfo.children):
                    if funcinfo.children[-1].type == sw_type.ANY:
                        var_length = 1
                    
                if not var_length and len(funcinfo.children) != len(src_node.children):
                    debug(rlt(funcinfo))
                    compiler_error(dest_node, f"The number of arguments passed to '&t' must be {len(funcinfo.children)}")
                    
                for idx, arg in enumerate(src_node.children):
                    arg_names.append(compile_node(arg, level))

                    if var_length:
                        if idx < len(funcinfo.children)-1 and not type_cmp(arg.tn, funcinfo.children[idx]) and not arg.tn.type == sw_type.INT:
                            compiler_error(arg, f"Vargument types don't match with function declaration: {hlt(funcinfo.children[idx])} != {hlt(arg.tn)}")
                        else:
                            debug("TYPE MATCHES", arg_names[idx], arg.tkname())
                    else:
                        if not type_cmp(arg.tn, funcinfo.children[idx]) and not arg.tn.type == sw_type.INT:
                            compiler_error(arg, f"Argument types don't match with function declaration: {hlt(funcinfo.children[idx])} != {hlt(arg.tn)}")
                        else:
                            debug("TYPE MATCHES", arg_names[idx], arg.tkname())
                if (funcinfo.type, funcinfo.ptrl) == (sw_type.VOID, 0):
                    out_write(f"call void {to_call}(", level); iota()
                else:
                    out_write(f"%{iota()} = call {rlt(ftn(funcinfo.type, funcinfo.ptrl))} {to_call}(", level)
                for idx, arg in enumerate(arg_names):
                    if idx:
                        out_write(", ", 0)
                    out_write(f"{rlt(src_node.children[idx].tn)} {arg}", 0)
                out_writeln(")", 0)
                
            else:
                for idx, arg in enumerate(node.children):
                    arg_names.append(compile_node(arg, level))
                    # # debug("types for node:", node.tkname(), hlt(node.tn.type, node.tn.ptrl), hlt(arg.tn.type, arg.tn.ptrl))
                    if not idx:
                        node.tn = arg.tn.copy() # operand type is type of the first operand
                
                if (src_node.tn.type, src_node.tn.ptrl) != (node.tn.type, node.tn.ptrl):
                    if src_node.tn.ptrl or node.tn.ptrl:
                        if node.tkname() in ("+","-","*","/","%"):
                            compiler_error(node, "cannot perform arithmetic operations on pointers, please cast to int, then back to pointers")
                        else:
                            compiler_error(node, "cannot perform logic operations on pointers, please cast to int, then back to pointers")
                    casted_src = cast(arg_names[1], src_node.tn, node.tn, level)[0]
                else:
                    casted_src = arg_names[1]

                match node.tkname():
                    case "+":
                        if both_ints(dest_node, src_node):
                            node.kind = kind.NUM_LIT
                            node.token = (*node.token[:-1], str(int(dest_node.tkname()) + int(src_node.tkname())))
                            return f"{node.tkname()}"
                        out_writeln(f"%{iota()} = add {rlt(node.tn)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "-":
                        if both_ints(dest_node, src_node):
                            node.kind = kind.NUM_LIT
                            node.token = (*node.token[:-1], str(int(dest_node.tkname()) - int(src_node.tkname())))
                            return f"{node.tkname()}"
                        out_writeln(f"%{iota()} = sub {rlt(node.tn)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "*":
                        if both_ints(dest_node, src_node):
                            node.kind = kind.NUM_LIT
                            node.token = (*node.token[:-1], str(int(dest_node.tkname()) * int(src_node.tkname())))
                            return f"{node.tkname()}"
                        out_writeln(f"%{iota()} = mul {rlt(node.tn)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "/":
                        if both_ints(dest_node, src_node):
                            node.kind = kind.NUM_LIT
                            node.token = (*node.token[:-1], str(int(dest_node.tkname()) // int(src_node.tkname())))
                            return f"{node.tkname()}"
                        out_writeln(f"%{iota()} = sdiv {rlt(node.tn)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"
                    case "%":
                        if both_ints(dest_node, src_node):
                            node.kind = kind.NUM_LIT
                            node.token[-1] = str(int(dest_node.tkname()) % int(src_node.tkname()))
                            return f"{node.tkname()}"
                        out_writeln(f"%{iota()} = srem {rlt(node.tn)} {arg_names[0]}, {casted_src}", level)
                        return f"%{iota(-1)}"

                    case ">":
                        out_writeln(f"%{iota()} = icmp sgt {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                    case "<":
                        out_writeln(f"%{iota()} = icmp slt {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                    case ">=":
                        out_writeln(f"%{iota()} = icmp sge {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                    case "<=":
                        out_writeln(f"%{iota()} = icmp sle {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                    case "==":
                        out_writeln(f"%{iota()} = icmp eq {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                    case "!=":
                        out_writeln(f"%{iota()} = icmp ne {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)

                    case "&":
                        out_writeln(f"%{iota()} = and {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "|":
                        out_writeln(f"%{iota()} = or {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"
                    case "^":
                        out_writeln(f"%{iota()} = xor {rlt(node.tn)} {arg_names[0]}, {arg_names[1]}", level)
                        return f"%{iota(-1)}"

                    case "&&":
                        lhs = cast(arg_names[0], node.children[0].tn, ftn(sw_type.BOOL, 0), nlevel)[0]
                        rhs = cast(arg_names[1], node.children[1].tn, ftn(sw_type.BOOL, 0), nlevel)[0]
                    
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

                        node.tn = ftn(sw_type.BOOL, 0)
                        return result_var


                    case "||":
                        lhs = cast(arg_names[0], node.children[0].tn, ftn(sw_type.BOOL, 0), nlevel)[0]
                        rhs = cast(arg_names[1], node.children[1].tn, ftn(sw_type.BOOL, 0), nlevel)[0]

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

                        node.tn.type, node.tn.ptrl = sw_type.BOOL, 0
                        return result_var

                if node.tkname() in [">", "<", ">=", "<=", "==", "!="]:
                    node.tn.type, node.tn.ptrl = sw_type.BOOL, 0
                    return f"%{iota(-1)}"


        case kind.GETPTR:
            name = compile_node(node.block, level, 1)
            node.kind = node.block.kind
            node.tn = node.block.tn+1
            return f"{name}"

        case kind.REFPTR:
            dest = compile_node(node.block, level)
            if not node.block.tn.ptrl:
                debug(hlt(node.block.tn))
                compiler_error(node, "Only pointers can be dereferenced")
            out_writeln(f"%{iota()} = getelementptr {rlt(ftn(node.block.tn.type, node.block.tn.ptrl-1))}, {rlt(ftn(node.block.tn.type, node.block.tn.ptrl))} {dest}, i64 0", level)
            if not assignable:
                out_writeln(f"%{iota()} = load {rlt(ftn(node.block.tn.type, node.block.tn.ptrl-1))}, {rlt(ftn(node.block.tn.type, node.block.tn.ptrl))} %{iota(-1)-1}", level)
                node.tn.type, node.tn.ptrl = node.block.tn.type, node.block.tn.ptrl-1
            else:
                node.tn.type, node.tn.ptrl = node.block.tn.type, node.block.tn.ptrl-1
            return f"%{iota(-1)}"
           
        case kind.EXTERN:
            out_write(f"declare {rlt(node.tn)} @{node.tkname()}(", level)
            for idx, arg in enumerate(node.children):
                if idx:
                    out_write(", ", 0)
                out_write(rlt(arg.tn), 0)
            out_writeln(")\n", 0)
        
        case kind.FUNCREF:
            return f"@{node.tkname()}"
        case kind.FUNCCALL:
            exit("Deprecated")
                    
        case kind.FUNCDECL:
            current_namespace = func_namespaces[node.tkname()]
            iota_counter = -1
            out_write(f"define {rlt(node.tn)} @{node.tkname()}(", level)
            for idx, arg in enumerate(node.children):
                if idx:
                    out_write(", ", 0)
                if arg.tn.type != sw_type.ANY:
                    out_write(f"{rlt(arg.tn)} %{iota()}", 0)
                else:
                    out_write(f"...", 0)
            out_writeln(") {", 0)
            iota_counter = -1
            for arg in node.children:
                if arg.tn.type != sw_type.ANY:
                    out_writeln(f"%{arg.tkname()} = alloca {rlt(arg.tn)}", nlevel)
                    out_writeln(f"store {rlt(arg.tn)} %{iota()}, ptr %{arg.tkname()}", nlevel)
            iota()
            ret = compile_node(node.block, nlevel)
            if node.block.kind != kind.RET or not len(node.block.children):
                if len(node.block.children) == 0:
                    if (node.tn.type, node.tn.ptrl) == (sw_type.VOID, 0):
                        out_writeln(f"ret {rlt(node.tn)}", nlevel)
                    else:
                        out_writeln(f"ret {rlt(node.tn)} {node.tn.get_zero()}", nlevel)

                elif not type_cmp(node.tn, node.block.children[-1].tn) and (node.tn.type, node.tn.ptrl) != (sw_type.VOID, 0):
                    if (node.block.children[-1].tn.type, node.block.children[-1].tn.ptrl) == (sw_type.VOID, 0):
                        out_writeln(f"ret {rlt(node.tn)} {node.tn.get_zero()}", nlevel)
                    else:
                        compiler_error(node.block.children[-1], f"return types don't match: function is of type '{hlt(node.tn)}' but '{hlt(node.block.children[-1].tn)}' was returned")
                else:
                    if (node.tn.type, node.tn.ptrl) == (sw_type.VOID, 0):
                        out_writeln("ret void", nlevel)
                    else:
                        out_writeln(f"ret {rlt(node.tn)} {ret}", nlevel)
            out_writeln("}\n", 0)
        
        case kind.STRUCT:
            out_write(f"%struct.{node.tkname()} = type {{", level)
            for idx, arg in enumerate(node.children):
                if idx:
                    out_write(", ", level)
                out_write(f"{rlt(arg.tn)}", level)
            out_writeln("}", level)
        
        case kind.IF:
            compiled_node = compile_node(node.block, nlevel)

            then_node = node.children[0]
            branch_id = iota()
            has_else = len(node.children) > 1

            condition = cast(compiled_node, node.block.tn, ftn(sw_type.BOOL, 0), level)[0]
            
            if has_else:
                else_node = node.children[1]
                out_writeln(f"br i1 {condition}, label %then.{branch_id}, label %else.{branch_id}", level)
            else:
                out_writeln(f"br i1 {condition}, label %then.{branch_id}, label %done.{branch_id}", level)
            out_writeln(f"then.{branch_id}:", level)
            ret = compile_node(then_node, nlevel)
            if has_else:
                if then_node.kind != kind.RET:
                    out_writeln(f"br label %done.{branch_id}", nlevel)
                out_writeln(f"else.{branch_id}:", level)
                ret = compile_node(else_node, nlevel)
                then_node = else_node # this is so that even when this branch is not ran, the code can continue with the then_node
            # debug("[BLOCK]->[RETURNED] -- kind =", human_kind[then_node.kind])
            if then_node.kind != kind.RET:
                out_writeln(f"br label %done.{branch_id}", nlevel)
            out_writeln(f"done.{branch_id}:", level)
            return ret

        case kind.WHILE:
            branch_id = iota()

            out_writeln(f"br label %cond.{branch_id}", level)
            out_writeln(f"cond.{branch_id}:", level)
            compiled_node = compile_node(node.children[0], nlevel)
            condition = cast(compiled_node, node.children[0].tn, ftn(sw_type.BOOL, 0), nlevel)[0]
            out_writeln(f"br i1 {condition}, label %loop.{branch_id}, label %done.{branch_id}", nlevel)
            out_writeln(f"loop.{branch_id}:", level)
            ret = compile_node(node.block, nlevel)
            out_writeln(f"br label %cond.{branch_id}", nlevel)
            out_writeln(f"done.{branch_id}:", level)
            return ret
        # purposelly: uncompilables - not compilable
        case kind.MACRODECL:
            if DEBUGGING:
                out_writeln("; '{node.tkname()}' macro declared here", level)
        
        case kind.WORD:
            if node.tkname() in current_namespace:
                node.kind = kind.VARREF
                node.tn = current_namespace[node.tkname()].tn
                return compile_node(node, level, assignable)
            compiler_error(node, "Unexpected unqualified token '&t' cannot be compiled")

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

# debug(declared_structs, "\n", human_type, "\n", [(x.tn.type, x.tn.ptrl) for key, x in declared_structs.items()])

compiler_call = f"{args.backend} {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module {args.b}"

debug("[INFO]: compiler call:", compiler_call)

os.system(compiler_call)
if not args.emit_llvm:
    os.system(f"del {OUTFILE_PATH}")
