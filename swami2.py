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
parse_level = 0
def debug(*arguments) -> None:
    if not DEBUGGING:
        return
    print(": "*parse_level, end="")
    for arg in arguments:
        print(arg, end=" ")
    print()

human_type = [
    "ptr",
    "int",
    "void",
    "char",
    "bool",
    "..",
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
    return human_type[type] + ("*"*ptr_level)

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
    ".."
]

def uisalnum(s: str) -> bool:
    return all(c.isalnum() or c == "_" for c in s)

def tokenizable(s: str) -> bool:
    return uisalnum(s) and not s[0].isnumeric() 

def find_next(line: str) -> int:
    for idx, c in enumerate(line):
        if c == "\"":
            debug("stringlt:",line[idx:])
            idx = line[idx+1:].find("\"")
            return max(1, idx+2)
        if c in human_operands and (idx == 0 or line[idx-1] == " "):
            debug("checking ", line[idx+1])
            if line[idx+1] in human_operands:
                debug(line[idx:idx+2], "is in human_ops")
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

@dataclass
class Node:
    value: str
    kind = -1
    args: list = []
    type = -1

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

class Manager:
    def __init__(self, items):
        self.items = items
        self.pointer = 0

    def next(self):
        return self.items[self.pointer+1]
    
    def inc(self):
        self.pointer += 1
    
    def current(self):
        return self.items[self.pointer]
    
    def consume(self):
        self.inc()
        return self.current()
    
    def set(self, nptr):
        self.pointer = nptr

parsed_tokens = lex_lines(INFILE_PATH)
tokens = Manager(parsed_tokens)

def get_importance(token):
    ...

def parse():
    return parse_expression(0)

def parse_primary():
    ...

def parse_expression(importance): # <- wanted to write priority
    node = parse_primary(tokens.current())

    while get_importance(tokens.next()) > importance:
        next_op = tokens.consume()
        old_node = node
        node = parse_primary(get_importance(next_op))
        node.args.append(old_node)
    
    return node

def parse_primary():
    token = tokens.consume()
    node = Node()

    if token[-1].isnumeric():
        node.kind = kind.NUM_LIT
        node.value = token[-1]
        return token

