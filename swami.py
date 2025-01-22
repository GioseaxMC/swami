from dataclasses import dataclass
from sys import *
argc = len(argv)

iota_counter = 0
def iota(reset: int = 0):
    global iota_counter
    iota_counter += 1
    if reset:
        iota_counter = 0
    return iota_counter

DEBUGGING = "-d" in argv
def debug(*arguments) -> None:
    if not DEBUGGING:
        return
    for arg in arguments:
        print(arg, end=" ")
    print()

def compiler_error(token, prompt, errno = -1):
    print(get_tk_pos(token)+":", "ERROR:", prompt.replace("&t", token[-1]))
    with open(token[0], "r") as fp:
        content = fp.read()
        print("\n  "+content.split("\n")[token[1]])
        print("  "+" "*token[2]+"^")
        print("  "+" "*token[2]+"| here")
    exit(errno)

def get_tk_name(token: tuple[str, int, int, str]):
    return token[-1]

def get_tk_pos(token: tuple[str, int, int, str]):
    return token[0]+":"+str(token[1]+1)+":"+str(token[2]+1)

def loud_call(func):
    def wrapper(*args, **kwargs):
        debug("Calling:", func.__name__)
        return func(*args, **kwargs)
    return wrapper

@dataclass
class kind:
    FUNC_CALL = iota(1)
    FUNC_DECL = iota()
    STR_LITER = iota()
    BODY = iota()
    VAR_DECL = iota()
    INT_LITER = iota()

@dataclass
class type:
    PTR  = iota(1)
    INT  = iota()
    VOID = iota()
    CHAR = iota()
    STR  = iota()

human_type = [
    "ptr",
    "int",
    "void",
    "char",
    "str",
]

def get_type(value: str) -> int:
    if value.isnumeric():
        return type.INT
    elif value[0] == "\"" and value[-1] == "\"":
        return type.STR
    elif value[0] == "'" and value[-1] == "'":
        return type.CHAR
    else:
        return type.PTR

def human_kind(kindex: int):
    return str(kindex)+":"+[
        "function call",
        "function declaration",
        "string literal",
        "body",
        "variable declaration",
        "int literal"
    ][kindex]

sw_builtins = { # name : type
    "print":"void"
}

sw_declared_funcs = dict()
sw_declared_vars  = dict()

def add_usr_func(name, type, token):
    global sw_declared_funcs
    if name not in sw_declared_funcs:
        sw_declared_funcs[name] = type
    else:
        compiler_error(token, "Redefinition of function '&t'")

def add_usr_var(name, type, token):
    global sw_declared_vars
    if name not in sw_declared_vars:
        sw_declared_vars[name] = type
    else:
        compiler_error(token, "Redefinition of variable '&t'")

string_literals = []
def add_string(tokens, index):
    string_literals.append(tokens[index][-1])
    return "string."+str(len(string_literals))

def find_nalnum(line: str) -> int:
    for idx, c in enumerate(line):
        if c == "\"":
            debug("stringlt:",line[idx:])
            idx = line[idx+1:].find("\"")
            return max(1, idx+2)
        if not c.isalnum():
            return max(1, idx)
    return -1

def lex_tokens(line: str) -> str:
    og_len = len(line)
    while len(line):
        sline = line.lstrip()
        col = og_len - len(sline)
        x = find_nalnum(sline)
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

OUTFILE_PATH = "./out.ll"
INFILE_PATH = "./main.sw"

if argc <= 1:
    debug("swami.py : usage")
    debug("    swami [input-file] -o <output-file>")
    debug("")
    debug("  - [required argument]")
    debug("  - <optional argument>")
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

class statement:
    def __init__(self):
        self.name = ""
        self.kind = -1
        self.type = ""
        self.children = []
        self.block = None
        self.value = None

def handle_statement(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    current_tk = tokens[index+0][-1]
    match current_tk:
        case ";"|"," :
            return None, index+1
        case "func":
            current_statement, index = handle_function_declaration(index+1, tokens)
        case "{":
            current_statement, index = handle_block(index+1, tokens)
        case _:
            if current_tk[-1] == "\"" and current_tk[0] == "\"":
                current_statement, index = handle_str_literal(index, tokens)
            elif current_tk[-1].isnumeric():
                current_statement, index = handle_num_literal(index, tokens)
            elif current_tk in human_type:
                current_statement, index = handle_var_decl(index, tokens)
            else:
                if current_tk in sw_builtins or current_tk in sw_declared_funcs:
                    current_statement, index = handle_function_call(index, tokens)
                else:
                    compiler_error(tokens[index], "Undeclared reference '&t'")
    return current_statement, index

@loud_call
def handle_block(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    blocker = statement()
    blocker.kind = kind.BODY
    blocker.children, index = handle_body(index, tokens)
    return blocker, index

@loud_call
def handle_body(index: int, tokens: tuple[str, int, int, str]) -> [list[statement], int]:
    statements = []
    while index < len(tokens) and tokens[index][-1] != "}":
        debug("body: Trying to handle", tokens[index][-1], "at", index)
        current_stm, index = handle_statement(index, tokens)
        if current_stm:
            statements.append(current_stm)
    return statements, index+1

@loud_call
def handle_num_literal(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    number = statement()
    number.type = type.STR
    number.kind = kind.INT_LITER
    number.name = tokens[index][-1]
    return number, index+1

@loud_call
def handle_str_literal(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    debug("Handling string literal")
    current_stm = statement()
    current_stm.name = add_string(tokens, index)
    current_stm.kind = kind.STR_LITER
    current_stm.type = type.STR
    return current_stm, index+1

@loud_call
def handle_var_decl(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    variable = statement()
    variable.type = human_type.index(tokens[index][-1])
    variable.kind = kind.VAR_DECL
    if variable.type == type.STR:
        if tokens[index+1][-1].isalnum():
            compiler_error(tokens[index], "type void cannot describe a value")
        index+=1
    else:
        index+=1
        variable.name = tokens[index][-1]
        if not variable.name.isalnum():
            compiler_error(tokens[index], "Token '&t' is not fit to be a variable name.")
        add_usr_var(variable.name, variable.type, tokens[index])
        index+=1
        if tokens[index][-1] == "=":
            index+=1
            variable.value = tokens[index][-1]
            if variable.type != get_type(variable.value):
                compiler_error(tokens[index],
                    f"Declared as '{human_type[variable.type]}' but received '{human_type[get_type(variable.value)]}'")
            index+=1
    return variable, index

@loud_call
def handle_statements(index: int, tokens: tuple[str, int, int, str]) -> [list[statement], int]:
    statements = []
    while index < len(tokens):
        debug("statement: Trying to handle", tokens[index][-1], "at", index)
        current_stm, index = handle_statement(index, tokens)
        if current_stm:
            statements.append(current_stm)
    return statements, index

@loud_call
def handle_function_call(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    function = statement()
    function.kind = kind.FUNC_CALL
    function.name = tokens[index][-1]
    index += 1
    token_btw_args = tokens[index][-1]
    while token_btw_args not in ")":
        if tokens[index+1][-1] == ")":
            break
        child_stm, index = handle_statement(index+1, tokens)
        function.children.append(child_stm)
        token_btw_args = tokens[index][-1]
    index+=1
    return function, index

@loud_call
def handle_function_declaration(index: int, tokens: tuple[str, int, int, str]) -> [statement, int]:
    function = statement()
    function.kind = kind.FUNC_DECL
    function.type = tokens[index][-1]
    index+=1
    function.name = tokens[index][-1]
    name_index = index
    index+=1
    add_usr_func(function.name, function.type, tokens[index-1])
    token_btw_args = tokens[index][-1]
    index+=1
    while token_btw_args not in ")":
        if tokens[index][-1] == ")":
            break
        child_stm, index = handle_statement(index, tokens)
        if child_stm:
            function.children.append(child_stm)
        token_btw_args = tokens[index][-1]
    index+=1
    
    if len(tokens) <= index:
        compiler_error(tokens[name_index], "Missing body for function '&t'")
    if tokens[index][-1] == "{":
        function.block, index = handle_block(index+1, tokens)
    return function, index

tokens = list(lex_lines(INFILE_PATH))
debug(tokens, "\n\n")
statements, _ = handle_statements(0, tokens)

def print_state(states: list[statement], level: int = 0):
    try:
        for state in states:
            debug(f"{" "*level*2}Name:", state.name);
            debug(f"{" "*level*2} -Type:", state.type);
            debug(f"{" "*level*2} -Kind:", human_kind(state.kind));
            debug(f"{" "*level*2} -Val :", state.value);
            if len(state.children):
                debug(f"{" "*level*2} -Args:");
                print_statements(state.children, level+1)
            if state.block:
                debug(f"{" "*level*2} -Block:");
                print_statements([state.block,], level+1)
        for key, type in sw_declared_vars:
            print(f"{type}: {key}")
        for key, type in sw_declared_funcs:
            print(f"{type}: {key}")
    except Exception as e:
        debug("Not printable:", e)

print_state(statements)

with open(OUTFILE_PATH, "w") as fp:
    fp.write("; llvm here")