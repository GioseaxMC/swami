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

def parser_error(token, prompt, errno = -1):
    print(get_tk_pos(token)+":", "ERROR:", prompt.replace("&t", token[-1]))
    with open(token[0], "r") as fp:
        content = fp.read()
        print("\n  "+content.split("\n")[token[1]])
        print("  "+" "*token[2]+"^")
        print("  "+" "*token[2]+"| here")
    exit(errno)

def compiler_error(state, prompt, errno = -1):
    ogToken = state.ogToken
    lastToken = state.lastToken
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

call_level = 0
def loud_call(func):
    global call_level;
    def wrapper(*args, **kwargs):
        global call_level
        call_level+=1
        debug("[CALL]:", func.__name__)
        ret = func(*args, **kwargs)
        call_level-=1
        debug("\\_ [ENDC]:", func.__name__)
        return ret
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
    OPERAND = iota()

@dataclass
class sw_type:
    PTR  = iota(1)
    INT  = iota()
    VOID = iota()
    CHAR = iota()
    STR  = iota()

stoppers = [";)}"]

human_type = [
    "ptr",
    "int",
    "void",
    "char",
    "str",
    "<->"
]

llvm_type = [
    "ptr",
    "i64",
    "void",
    "i8",
    "i8*",
    "<->"
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
        "variable reference",
        "operand"
    ][kindex]

sw_builtins = { # name : type
    "print" : sw_type.VOID,
    "println" : sw_type.VOID,
    "printf" : sw_type.VOID
}

@dataclass
class INTRINSIC:
    RET = iota(1)
    LLVM = iota()

human_intrinsic = [
    "return",
    "llvm"
]

llvm_intrinsic = [
    "ret",
    ""
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
        parser_error(token, "Redefinition of function '&t'")

def add_usr_var(name, type, token):
    global sw_declared_vars
    if name not in sw_declared_vars:
        sw_declared_vars[name] = type
    else:
        parser_error(token, "Redefinition of variable '&t'")

human_operands = "=+-*/"

string_literals = {}
def add_string(tokens, index):
    string_literals["str."+str(len(string_literals)+1)] = tokens[index][-1]
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
        self.ogToken = None

def parse_statement(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    current_tk = tokens[index+0][-1]
    ogToken = tokens[index]
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
            elif current_tk.isnumeric():
                current_statement, index = parse_num_literal(index, tokens)
            elif current_tk in human_type:
                current_statement, index = parse_var_decl(index, tokens)
            elif current_tk in human_intrinsic:
                current_statement, index = parse_intrinsic(index, tokens)
            else:
                if current_tk in sw_builtins or current_tk in sw_declared_funcs:
                    current_statement, index = parse_function_call(index, tokens)
                elif current_tk in sw_declared_vars:
                    current_statement, index = parse_var_reference(index, tokens)
                elif current_tk in human_operands:
                    current_statement, index = parse_operand(index, tokens)
                else:
                    if current_tk.isalnum():
                        parser_error(tokens[index], "'&t' is undefined")
                    else:
                        parser_error(tokens[index], "Unexpected token '&t'")
    current_statement.ogToken = ogToken
    current_statement.lastToken = tokens[index-1]
    return current_statement, index

@loud_call
def parse_block(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    blocker = statement()
    blocker.kind = kind.BODY
    blocker.args, index = parse_body(index, tokens, "}")
    return blocker, index

@loud_call
def parse_body(index: int, tokens: tuple[str, int, int, str], stop_at, safefail_on="") -> tuple[list[statement], int]:
    statements = []
    while index < len(tokens) and tokens[index][-1] not in stop_at:
        if tokens[index][-1] in stoppers:
            compiler_error(tokens[index], "Closing unopned block '&t'")
        if tokens[index][-1] == safefail_on:
            debug(f"body({stop_at}): [SAFEFAIL]: tobeparsed:", tokens[index][-1], "at", index)
            return statements, index
        debug(f"body({stop_at}): Trying to parse", tokens[index][-1], "at", index)
        current_stm, index = parse_statement(index, tokens)
        if index < len(tokens):
            debug(f"body({stop_at}): [NEXT]: tobeparsed:", tokens[index][-1], "at", index)
        if current_stm:
            statements.append(current_stm)
    debug(f"body({stop_at}): [DONE]: Done parsing body")
    return statements, index+1

@loud_call
def parse_intrinsic(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    intrinsic = statement()
    if tokens[index][-1] in human_intrinsic:
        intrinsic.name = tokens[index][-1]
        intrinsic.kind = kind.INTRINSIC
        intrinsic.type = human_intrinsic.index(tokens[index][-1])
        index+=1
        intrinsic.args, index = parse_body(index, tokens, ";")
    return intrinsic, index


@loud_call
def parse_num_literal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    number = statement()
    number.type = sw_type.INT
    number.kind = kind.INT_LITER
    number.value = tokens[index][-1]
    return number, index+1

@loud_call
def parse_str_literal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
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
            parser_error(tokens[index], "type void cannot describe a value")
        index+=1
    else:
        index+=1
        variable.name = tokens[index][-1]
        if not uisalnum(variable.name):
            parser_error(tokens[index], "Token '&t' is not fit to be a variable name.")
        add_usr_var(variable.name, variable.type, tokens[index])
        index+=1
        if tokens[index][-1] == "=":
            index+=1
            debug("var_decl: Trying to parse", tokens[index][-1], "at", index)
            variable.args, index = parse_body(index, tokens, ";")
            # if variable.type != variable.args:
            #     parser_error(tokens[index],
            #         f"Declared as '{human_type[variable.type]}' but received '{human_type[variable.args[0].type]}'")
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
    variable.type = sw_declared_vars[tokens[index][-1]]
    variable.name = tokens[index][-1]
    index+=1
    return variable, index

@loud_call
def parse_operand(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    operand = statement()
    operand.kind = kind.OPERAND
    operand.name = tokens[index][-1]
    index+=1
    debug("operand: Trying to parse", tokens[index][-1], "at", index)
    if operand.name == "=":
        operand.args, index = parse_body(index, tokens, ";")
    else:
        arg_stm, index = parse_statement(index, tokens)
        operand.args.append(arg_stm)
    debug("operand: [DONE]: tobeparsed:", tokens[index][-1], "at", index)
    return operand, index

@loud_call
def parse_function_call(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    function = statement()
    function.kind = kind.FUNC_CALL
    function.name = tokens[index][-1]
    index+=1
    if tokens[index][-1] == "(":
        index+=1
        while tokens[index][-1] != ")":
            current_exp = statement()
            current_exp.args, index = parse_body(index, tokens, ",", ")")
            function.args.append(current_exp)
    else:
        parser_error(tokens[index], "Missing arguments for function '&t'")
    return function, index+1

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
    if tokens[index][-1] == "(":
        function.args, index = parse_body(index+1, tokens, ")")
    else:
        parser_error(tokens[index], "Missing arguments for function '&t'")
    
    if len(tokens) <= index:
        parser_error(tokens[name_index], "Missing body for function '&t'")
    if tokens[index][-1] == "{":
        function.block, index = parse_block(index+1, tokens)
    return function, index

tokens = list(lex_lines(INFILE_PATH))
debug(tokens, "\n\n")
statements, _ = parse_statements(0, tokens)

if not len(statements):
    parser_error((INFILE_PATH,0,2,""), "No statements found in the file, consider creating a main entry point.\n\n    - Are you happy now, Rexim?\n\n    expected:\n\n    func int main() {\n      return 0;\n    }")
if "main" not in sw_declared_funcs:
    parser_error((INFILE_PATH,0,0,""), "No main entry point found in the file, consider creating a main entry point.\n\n    expected:\n\n    func int main() {\n      return 0;\n    }")
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

available_func = dict()
available_func.update(sw_builtins)
available_func.update(sw_declared_funcs)
def compile_statement(state, level: int = 0):
    nlevel = level+1
    type_liota = []
    current_type_iota = None
    match state.kind:
        
        case kind.FUNC_CALL:
            debug("Compiling function call:", state.name)
            # out_writeln(f"; Function call: {state.name}", level)
            for argstate in state.args:
                for arg in argstate.args:
                    current_type_iota = compile_statement(arg, level)
                type_liota.append(current_type_iota)
            if available_func[state.name] == sw_type.VOID:
                out_write(f"call void @{state.name}(", level)
            else:
                out_write(f"%{iota()} = call {llvm_type[available_func[state.name]]} @{state.name}(", level)
            for idx, (viota, vtype) in enumerate(type_liota):
                if idx:
                    out_write(", ")
                out_write(f"{vtype} %{viota}")
            out_writeln(")")
            return iota(-1), llvm_type[available_func[state.name]]
        
        case kind.FUNC_DECL:
            debug("Compiling function declaration:", state.name)
            # out_writeln(f"; Function declaration: {state.name}", level)
            out_write(f"\ndefine {llvm_type[state.type]} @{state.name}(", level)
            for idx, arg in enumerate(state.args):
                out_write(f"{llvm_type[arg.type]} %{iota()}")
                if idx+1 != len(state.args):
                    out_write(", ")
            len_args = len(state.args)
            out_write(") {\n")
            for idx, arg in enumerate(state.args):
                out_writeln(f"%{arg.name} = alloca {llvm_type[arg.type]}", nlevel)
                out_writeln(f"store {llvm_type[arg.type]} %{iota()-len_args}, ptr %{arg.name}", nlevel)
            for stm in state.block.args:
                compile_statement(stm, nlevel)
            # out_writeln("ret i64 0", nlevel)
            out_write("\n}\n")
        
        case kind.INT_LITER:
            debug("Compiling int literal:", state.value)
            # out_writeln(f"; Int literal: {state.value}", level)
            out_writeln(f"%{iota()} = add i64 {state.value}, 0", level)
            return iota(-1), llvm_type[sw_type.INT]
        
        case kind.STR_LITER:
            debug("Compiling string literal:", state.name)
            # out_writeln(f"; Str literal: {state.name}", level)
            out_writeln(f"%{iota()} = load ptr, ptr @{state.name}.ptr", level)
            return iota(-1), llvm_type[sw_type.STR]
        
        case kind.VAR_DECL:
            debug("Compiling variable declaration:", state.name)
            # out_writeln(f"; Variable declaration: {state.name}", level)
            sw_declared_v_lvl[state.name] = level
            if level == 0:
                if state.value:
                    out_writeln(f"@{state.name} = global {llvm_type[state.type]} {state.value}")
                else:
                    out_writeln(f"@{state.name} = global {llvm_type[state.type]} 0")
            else:
                out_writeln(f"%{state.name} = alloca {llvm_type[state.type]}", level)
                for arg in state.args:
                    viota, vtype = compile_statement(arg, level)
                if len(state.args):
                    if vtype != llvm_type[state.type]:
                        compiler_error(state, f"Declared as '{human_type[state.type]}' but received '{human_type[llvm_type.index(vtype)]}'")
                    out_writeln(f"store {vtype} %{viota}, ptr %{state.name}", level)
        
        case kind.VAR_REF:
            debug("Compiling variable reference:", state.name)
            # out_writeln(f"; Variable reference: {state.name}", level)
            if sw_declared_v_lvl.get(state.name) == 0:
                out_writeln(f"%{iota()} = bitcast ptr @{state.name} to ptr", level)
                out_writeln(f"%{iota()} = load {llvm_type[sw_declared_vars[state.name]]}, ptr %{iota(-1)-1}", level)
            else:
                out_writeln(f"%{iota()} = bitcast ptr %{state.name} to ptr", level)
                out_writeln(f"%{iota()} = load {llvm_type[sw_declared_vars[state.name]]}, ptr %{iota(-1)-1}", level)
            return iota(-1), llvm_type[sw_declared_vars[state.name]]
        
        case kind.INTRINSIC:
            debug("Compiling intrinsic:", state.name)
            # out_writeln(f"; Intrinsic: {state.name}", level)
            match state.type:
                case INTRINSIC.RET:
                    for arg in state.args:
                        current_type_iota = compile_statement(arg, level)
                    out_write(f"{llvm_intrinsic[state.type]}", level)
                    if len(state.args):
                        type_liota.append(current_type_iota)
                    else:
                        out_write(" void")

                    for idx, (viota, vtype) in enumerate(type_liota):
                        if idx:
                            out_write(",")
                        out_write(f" {vtype} %{viota}")
                case INTRINSIC.LLVM:
                    debug("Compiling LLVM intrinsic:", state.name)
                    if len(state.args) != 1:
                        compiler_error(state, f"Intrinsic '&t' expects one and only one argument, but {len(state.args)} were given.")
                    out_writeln(string_literals[state.args[0].name][1:-1], level)
                    string_literals.pop(state.args[0].name)

        case kind.OPERAND:
            debug("Compiling operand:", state.name)
            # out_writeln(f"; Operand: {state.name}", level)
            varPtr = iota(-1)-1
            varVal = iota(-1)
            for arg in state.args:
                viota, vtype = compile_statement(arg, level)
            if state.name == "=":
                out_writeln(f"store {vtype} %{viota}, ptr %{varPtr}", level)
            match state.name:
                case "+":
                    out_writeln(f"%{iota()} = add {vtype} %{varVal}, %{viota}", level)
                case "-":
                    out_writeln(f"%{iota()} = sub {vtype} %{varVal}, %{viota}", level)
                case "*":
                    out_writeln(f"%{iota()} = mul {vtype} %{varVal}, %{viota}", level)
                case "/":
                    out_writeln(f"%{iota()} = sdiv {vtype} %{varVal}, %{viota}", level)
            debug("Operand:", state.name, "done")
            return iota(-1), vtype

out_writeln(f"""; FILE: {INFILE_PATH}

declare void @printf(i8*, ...)
define void @print(i8* %{iota()}) {{ call void (i8*, ...) @printf(i8* %{iota(-1)}) ret void }}
define void @println(i8* %{iota()}) {{ call void (i8*, ...) @printf(i8* %{iota(-1)}) call void @printf(i8* @newl) ret void }}
""")

iota(1)
for state in statements:
    compile_statement(state)

out_writeln()
for idx, string in string_literals.items():
    out_writeln(f"@{idx} = constant [{len(string)-1} x i8] c\"{string[1:-1]}\\00\"")
    out_writeln(f"@{idx}.ptr = global ptr @{idx}")

out_writeln(f"@newl = constant [2 x i8] c\"\\0A\\00\"")

# for idx, (key, vtype) in enumerate(sw_declared_vars.items()):
#     out_writeln(f"@{key} = global {llvm_type[vtype]} 0")

out.close()

os.system(f"clang {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module -target x86_64-64w-mingw32")