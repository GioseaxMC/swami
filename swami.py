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
    INTRINSIC = iota()
    VAR_REF = iota()

@dataclass
class sw_type:
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
    "something else"
]

llvm_type = [
    "ptr",
    "i64",
    "void",
    "i8",
    "i8*",
    "something else"
]

def get_type(value: str) -> int:
    if value.isnumeric():
        return sw_type.INT
    elif value[0] == "\"" and value[-1] == "\"":
        return sw_type.STR
    elif value[0] == "'" and value[-1] == "'":
        return sw_type.CHAR
    else:
        return -1

def human_kind(kindex: int):
    return str(kindex)+":"+[
        "function call",
        "function declaration",
        "string literal",
        "body",
        "variable declaration",
        "int literal",
        "intrinsic",
        "variable reference"
    ][kindex]

sw_builtins = { # name : type
    "print" : sw_type.VOID,
    "println" : sw_type.VOID,
    "printf" : sw_type.VOID
}

@dataclass
class INTRINSIC:
    RET = iota(1)

human_intrinsic = [
    "return"
]

llvm_intrinsic = [
    "ret"
]

sw_declared_funcs = dict()
sw_declared_f_lvl = dict() # maybe for future use
sw_declared_vars  = dict()
sw_declared_v_lvl = dict()

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

human_operands = "=+-*/"

string_literals = []
def add_string(tokens, index):
    string_literals.append(tokens[index][-1])
    return "str."+str(len(string_literals))

def uisalnum(s: str) -> bool:
    return all(c.isalnum() or c == "_" for c in s)

def find_nalnum(line: str) -> int:
    for idx, c in enumerate(line):
        if c == "\"":
            debug("stringlt:",line[idx:])
            idx = line[idx+1:].find("\"")
            return max(1, idx+2)
        if not uisalnum(c):
            return max(1, idx)
    return -1

def lex_tokens(line: str):
    og_len = len(line)
    while len(line) and not line.isspace():
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
        self.type = -1
        self.args = []
        self.block = None
        self.value = None

def parse_statement(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    current_tk = tokens[index+0][-1]
    match current_tk:
        case ";"|"," :
            return None, index+1
        case "func":
            current_statement, index = parse_function_declaration(index+1, tokens)
        case "{":
            current_statement, index = parse_block(index+1, tokens)
        case _:
            if current_tk[-1] == "\"" and current_tk[0] == "\"":
                current_statement, index = parse_str_literal(index, tokens)
            elif current_tk[-1].isnumeric():
                current_statement, index = parse_num_literal(index, tokens)
            elif current_tk in human_type:
                current_statement, index = parse_var_decl(index, tokens)
            elif current_tk in human_intrinsic:
                current_statement, index = parse_intrinsic(index, tokens)
            else:
                if current_tk in sw_builtins or current_tk in sw_declared_funcs:
                    current_statement, index = parse_function_call(index, tokens)
                elif current_tk in sw_declared_vars:
                    if 0:#tokens[index+1] in "=+/-*":
                        current_statement, index = parse_intrinsic(index, tokens)
                    else:
                        current_statement, index = parse_var_reference(index, tokens)
                else:
                    compiler_error(tokens[index], "Unexpected token '&t'")
    return current_statement, index

@loud_call
def parse_block(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    blocker = statement()
    blocker.kind = kind.BODY
    blocker.args, index = parse_body(index, tokens)
    return blocker, index

@loud_call
def parse_body(index: int, tokens: tuple[str, int, int, str]) -> tuple[list[statement], int]:
    statements = []
    while index < len(tokens) and tokens[index][-1] != "}":
        debug("body: Trying to parse", tokens[index][-1], "at", index)
        current_stm, index = parse_statement(index, tokens)
        if index < len(tokens):
            debug("body: tobeparsed:", tokens[index][-1], "at", index)
        if current_stm:
            statements.append(current_stm)
    return statements, index+1

@loud_call
def parse_intrinsic(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    intrinsic = statement()
    if tokens[index][-1] in human_intrinsic:
        intrinsic.name = tokens[index][-1]
        intrinsic.kind = kind.INTRINSIC
        intrinsic.type = human_intrinsic.index(tokens[index][-1])
        index+=1
        while tokens[index][-1] != ";":
            new_stm, index = parse_statement(index, tokens)
            intrinsic.args.append(new_stm)
        index+=1
    # elif tokens[index+1][-1] in human_operands:
    #     index+=1
    #     intrinsic.name = tokens[index][-1]
    #     intrinsic.kind = kind.INTRINSIC
    #     intrinsic.type = human_intrinsic.index(tokens[index][-1])
    #     index+=1
    #     while tokens[index][-1] != ";":
    #         new_stm, index = parse_statement(index, tokens)
    #         intrinsic.args.append(new_stm)
        
    return intrinsic, index


@loud_call
def parse_num_literal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    number = statement()
    number.type = sw_type.STR
    number.kind = kind.INT_LITER
    number.name = tokens[index][-1]
    return number, index+1

@loud_call
def parse_str_literal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    debug("Handling string literal")
    current_stm = statement()
    current_stm.name = add_string(tokens, index)
    current_stm.kind = kind.STR_LITER
    current_stm.type = sw_type.STR
    return current_stm, index+1

@loud_call
def parse_var_decl(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    variable = statement()
    variable.type = human_type.index(tokens[index][-1])
    variable.kind = kind.VAR_DECL
    if variable.type == sw_type.VOID:
        if tokens[index+1][-1].isalnum():
            compiler_error(tokens[index], "type void cannot describe a value")
        index+=1
    else:
        index+=1
        variable.name = tokens[index][-1]
        if not uisalnum(variable.name):
            compiler_error(tokens[index], "Token '&t' is not fit to be a variable name.")
        add_usr_var(variable.name, variable.type, tokens[index])
        index+=1
        if tokens[index][-1] == "=":
            index+=1
            if variable.type == sw_type.STR:
                variable.value = add_string(tokens, index)
            else:
                variable.value = tokens[index][-1]
                if variable.type != get_type(variable.value):
                    compiler_error(tokens[index],
                        f"Declared as '{human_type[variable.type]}' but received '{human_type[get_type(variable.value)]}'")
            index+=1
    return variable, index

@loud_call
def parse_statements(index: int, tokens: tuple[str, int, int, str]) -> tuple[list[statement], int]:
    statements = []
    while index < len(tokens):
        debug("statement: Trying to parse", tokens[index][-1], "at", index)
        current_stm, index = parse_statement(index, tokens)
        if current_stm:
            statements.append(current_stm)
    return statements, index

@loud_call
def parse_var_reference(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    variable = statement()
    variable.kind = kind.VAR_REF
    variable.name = tokens[index][-1]
    index+=1
    return variable, index

@loud_call
def parse_function_call(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    function = statement()
    function.kind = kind.FUNC_CALL
    function.name = tokens[index][-1]
    index += 1
    token_btw_args = tokens[index][-1]
    while token_btw_args not in ")":
        if tokens[index+1][-1] == ")":
            break
        child_stm, index = parse_statement(index+1, tokens)
        function.args.append(child_stm)
        token_btw_args = tokens[index][-1]
    index+=1
    return function, index

@loud_call
def parse_function_declaration(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    function = statement()
    function.kind = kind.FUNC_DECL
    function.type = human_type.index(tokens[index][-1])
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
        child_stm, index = parse_statement(index, tokens)
        if child_stm:
            function.args.append(child_stm)
        token_btw_args = tokens[index][-1]
    index+=1
    
    if len(tokens) <= index:
        compiler_error(tokens[name_index], "Missing body for function '&t'")
    if tokens[index][-1] == "{":
        function.block, index = parse_block(index+1, tokens)
    return function, index

tokens = list(lex_lines(INFILE_PATH))
debug(tokens, "\n\n")
statements, _ = parse_statements(0, tokens)

def print_state(states: list[statement], level: int = 0):
    nlevel = level+1
    try:
        for state in states:
            debug(f"{" "*level*2}Name:", state.name);
            debug(f"{" "*level*2} -Type:", human_type[state.type]);
            debug(f"{" "*level*2} -Kind:", human_kind(state.kind));
            debug(f"{" "*level*2} -Val :", state.value);
            if len(state.args):
                debug(f"{" "*level*2} -Args:");
                print_state(state.args, nlevel)
            if state.block:
                debug(f"{" "*level*2} -Block:");
                print_state([state.block,], nlevel)
    except Exception as e:
        debug("Not printable:", e)

print_state(statements)
for key, type in sw_declared_vars.items():
    debug(f"{type}: {key}")
for key, type in sw_declared_funcs.items():
    debug(f"{type}: {key}")

iota(1)
out = open(OUTFILE_PATH, "w")
def out_writeln(line: str = "", level: int = 0):
    out.write((" "*level*2)+line+"\n")
def out_write(line: str = "", level: int = 0):
    out.write((" "*level*2)+line)

sw_builtins.update(sw_declared_funcs)
def compile_statement(state, level: int = 0):
    nlevel = level+1
    type_liota = []
    match state.kind:
        case kind.FUNC_CALL:
            debug("Compiling function call:", state.name)
            for arg in state.args:
                type_liota.append(compile_statement(arg, level))
            out_write(f"call {llvm_type[sw_builtins[state.name]]} @{state.name}(", level)
            for idx, (viota, vtype) in enumerate(type_liota):
                if idx:
                    out_write(", ")
                out_write(f"{vtype} %{viota}")
            out_writeln(")")
        case kind.FUNC_DECL:
            debug("Compiling function declaration:", state.name)
            out_write(f"\ndefine {llvm_type[state.type]} @{state.name}(", level)
            for arg in state.args:
                compile_statement(arg, nlevel)
            out_write(") {\n")
            for stm in state.block.args:
                compile_statement(stm, nlevel)
            out_write("\n}\n", level)
        case kind.INT_LITER:
            debug("Compiling int literal:", state.name)
            out_writeln(f"%{iota()} = add i64 {state.name}, 0", level)
            return iota(-1), llvm_type[sw_type.INT]
        case kind.STR_LITER:
            debug("Compiling string literal:", state.name)
            out_writeln(f"%{iota()} = load ptr, ptr @{state.name}.ptr", level)
            return iota(-1), llvm_type[sw_type.STR]
        case kind.VAR_DECL:
            debug("Compiling variable declaration:", state.name)
            sw_declared_v_lvl[state.name] = level
            if level == 0:
                if state.value:
                    out_writeln(f"@{state.name} = global {llvm_type[state.type]} {state.value}", level)
                else:
                    out_writeln(f"@{state.name} = global {llvm_type[state.type]}", level)
            else:
                out_writeln(f"%{state.name} = alloca {llvm_type[state.type]}", level)
                if state.value:
                    out_writeln(f"store {llvm_type[state.type]} {state.value}, ptr %{state.name}", level)
        case kind.VAR_REF:
            debug("Compiling variable reference:", state.name)
            if sw_declared_v_lvl.get(state.name) == 0:
                out_writeln(f"%{iota()} = load {llvm_type[sw_declared_vars[state.name]]}, ptr @{state.name}", level)
            else:
                out_writeln(f"%{iota()} = load {llvm_type[sw_declared_vars[state.name]]}, ptr %{state.name}", level)
            return iota(-1), llvm_type[sw_declared_vars[state.name]]
        case kind.INTRINSIC:
            debug("Compiling intrinsic:", state.name)
            for arg in state.args:
                type_liota.append(compile_statement(arg, level))
            out_write(f"{llvm_intrinsic[state.type]}", level)
            for idx, (viota, vtype) in enumerate(type_liota):
                if idx:
                    out_write(",")
                out_write(f"{vtype} %{viota}", level)

out_writeln(f"""; file: {INFILE_PATH}

declare void @printf(i8*, ...)
define void @print(i8* %{iota()}) {{ call void (i8*, ...) @printf(i8* %{iota_counter}) ret void }}
define void @println(i8* %{iota()}) {{ call void (i8*, ...) @printf(i8* %{iota_counter}) call void @printf(i8* @newl) ret void }}
""")


for idx, string in enumerate(string_literals):
    out_writeln(f"@str.{idx+1} = constant [{len(string)-1} x i8] c\"{string[1:-1]}\\00\"")
    out_writeln(f"@str.{idx+1}.ptr = global ptr @str.{idx+1}")
out_writeln(f"@newl = constant [2 x i8] c\"\\0A\\00\"")

# for idx, (key, vtype) in enumerate(sw_declared_vars.items()):
#     out_writeln(f"@{key} = global {llvm_type[vtype]} 0")

for state in statements:
    compile_statement(state)

out.close()

os.system(f"clang {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module -target x86_64-64w-mingw32")