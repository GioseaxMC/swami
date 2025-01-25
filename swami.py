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
    if errno:
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
    BLOCK = iota()
    VAR_DECL = iota()
    INT_LITER = iota()
    INTRINSIC = iota()
    VAR_REF = iota()
    OPERAND = iota()
    BRANCH = iota()
    EXPRESSION = iota()

@dataclass
class sw_type:
    PTR  = iota(1)
    INT  = iota()
    VOID = iota()
    CHAR = iota()
    STR  = iota()
    BOOL  = iota()

stoppers = [";)}"]

human_type = [
    "ptr",
    "int",
    "void",
    "char",
    "str",
    "bool",
    "<->"
]

llvm_type = [
    "ptr",
    "i64",
    "void",
    "i8",
    "i8*",
    "i1",   
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

human_kind = [
    "function call",
    "function declaration",
    "string literal",
    "body",
    "variable declaration",
    "int literal",
    "intrinsic",
    "variable reference",
    "operand",
    "branch",
    "expression",

    "-not assigned"
]

sw_builtins = { # name : type
    "print" : sw_type.VOID,
    "println" : sw_type.VOID,
    "printf" : sw_type.VOID,
    "exit" : sw_type.VOID
}

@dataclass
class INTRINSIC:
    RET = iota(1)
    LLVM = iota()
    INCLUDE = iota()

human_intrinsic = [
    "return",
    "llvm",
    "include"
]

human_branch = [
    "if",
    "else",
    "while"
]

llvm_intrinsic = [
    "ret",
    "",
    ""
]

sw_declared_funcs = dict()
sw_declared_args = {
    "printf" : -1,
    "println" : 1,
    "print" : 1
} # maybe for future use \ no wayy
sw_declared_vars  = dict()
sw_declared_v_lvl = dict()

def add_usr_func(name, type, token, length):
    global sw_declared_funcs
    if name not in sw_declared_funcs:
        sw_declared_funcs[name] = type
        sw_declared_args[name] = length
    else:
        parser_error(token, "Redefinition of function '&t'")

def add_usr_var(name, type, token):
    global sw_declared_vars
    if name not in sw_declared_vars:
        sw_declared_vars[name] = type
    else:
        parser_error(token, "Redefinition of variable '&t'")

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
    "<="
]

string_literals = {}
def add_string(tokens, index):
    string_literals["str."+str(len(string_literals)+1)] = tokens[index][-1]
    return "str."+str(len(string_literals))

def uisalnum(s: str) -> bool:
    return all(c.isalnum() or c == "_" for c in s)

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
        self.subtype = -1
        self.args = []
        self.block = None
        self.value = None
        self.ogToken = None

statements: list[statement] = []

def parse_statement(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    current_tk = tokens[index+0][-1]
    ogToken = tokens[index]
    current_statement = statement()
    match current_tk:
        case ";"|"," :
            return None, index+1
        case "func":
            current_statement, index = parse_function_declaration(index+1, tokens)
        case "{":
            current_statement, index = parse_block(index+1, tokens)
        case "(":
            current_statement, index = parse_expression(index, tokens)
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
                elif current_tk in human_branch:
                    current_statement, index = parse_branch(index, tokens)
                else:
                    if uisalnum(current_tk):
                        parser_error(tokens[index], "'&t' is undefined")
                    else:
                        return statement(), -1;
    current_statement.ogToken = ogToken
    current_statement.lastToken = tokens[index-1]
    return current_statement, index

@loud_call
def parse_block(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    blocker = statement()
    blocker.kind = kind.BLOCK
    blocker.args, index = parse_body(index, tokens, "}")
    return blocker, index

@loud_call
def parse_expression(index: int, tokens: tuple[str, int, int, str]) -> tuple[list[statement], int]:
    index+=1
    expression = statement()
    expression.kind = kind.EXPRESSION
    expression.args, index = parse_body(index, tokens, ")")
    return expression, index

@loud_call
def parse_body(index: int, tokens: tuple[str, int, int, str], stop_at, safefail_on="") -> tuple[list[statement], int]:
    statements = []
    start = index-1
    while index < len(tokens) and tokens[index][-1] not in stop_at:
        if tokens[index][-1] in stoppers:
            parser_error(tokens[index], "Closing un-opened block '&t'")
        if tokens[index][-1] == safefail_on:
            debug(f"body({stop_at}): [SAFEFAIL]: tobeparsed:", tokens[index][-1], "at", index)
            return statements, index
        debug(f"body({stop_at}): Trying to parse", tokens[index][-1], "at", index)
        current_stm, index = parse_statement(index, tokens)
        if index < 0:
            parser_error(tokens[start], f"Expression must have the closing token '{stop_at}'")
        if index < len(tokens):
            debug(f"body({stop_at}): [NEXT]: tobeparsed:", tokens[index][-1], "at", index)
        if current_stm:
            statements.append(current_stm)
    index+=1
    if index > len(tokens):
        parser_error(tokens[start], f"Expression must be closed with '{stop_at}'")
    debug(f"body({stop_at}): [DONE]: Done parsing body")
    return statements, index

@loud_call
def parse_intrinsic(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    global statements
    intrinsic = statement()
    if tokens[index][-1] == "include":
        intrinsic.name = tokens[index][-1]
        intrinsic.kind = kind.INTRINSIC
        intrinsic.subkind = human_intrinsic.index(tokens[index][-1])
        index+=1
        intrinsic.args, index = parse_body(index, tokens, ";")
        for arg in intrinsic.args:
            included_path = string_literals[arg.name][1:-1]
            inc_tokens = list(lex_lines(included_path))
            debug(inc_tokens, "\n\n")
            inc_statements, _ = parse_statements(0, inc_tokens)
        debug("states before:", statements)
        statements += inc_statements
        debug("states AFTER:", statements)

    else:
        intrinsic.name = tokens[index][-1]
        intrinsic.kind = kind.INTRINSIC
        intrinsic.subkind = human_intrinsic.index(tokens[index][-1])
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
        if variable.name[0].isnumeric() or not uisalnum(variable.name):
            parser_error(tokens[index], "Token '&t' is not fit to be a variable name.")
        if variable.name in sw_builtins or variable.name in (human_intrinsic+human_branch+human_type):
            parser_error(tokens[index], "Token '&t' is a reserved keyword and cannot be a variable name.")
        add_usr_var(variable.name, variable.type, tokens[index])
        index+=1
        if tokens[index][-1] == "=":
            index+=1
            debug("var_decl: Trying to parse", tokens[index][-1], "at", index)
            variable.args, index = parse_body(index, tokens, ";")
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
    if operand.name == "!":
        current_stm, index = parse_statement(index, tokens);
        operand.args.append(current_stm)
    else:
        arg_stm, index = parse_statement(index, tokens)
        if arg_stm:
            operand.args.append(arg_stm)
    debug("operand: [DONE]: tobeparsed:", tokens[index][-1], "at", index)
    return operand, index

@loud_call
def parse_branch(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    branch = statement()
    branch.kind = kind.BRANCH
    branch.name = tokens[index][-1]
    index+=1
    if branch.name == "if":
        current_stm, index = parse_statement(index, tokens)
        branch.args.append(current_stm)
        branch.block, index = parse_statement(index, tokens)
        debug("[BRCH]: checking if is else")
        if tokens[index][-1] == "else":
            current_stm, index = parse_statement(index+1, tokens)
            branch.args.append(current_stm)
    elif branch.name == "else":
        parser_error(tokens[index], "Branch 'else' can only be used after 'if'")
    elif branch.name == "while":
        current_stm, index = parse_statement(index, tokens)
        branch.args.append(current_stm)
        block_start = index
        branch.block, index = parse_statement(index, tokens)
        if branch.block.kind == kind.BLOCK and not len(branch.block.args):
            parser_error(tokens[block_start], "While body cannot be empty")
    else:
        parser_error(tokens[index], "Branch '&t' is not implemented yet")
    return branch, index

@loud_call
def parse_function_call(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    function = statement()
    function.kind = kind.FUNC_CALL
    function.name = tokens[index][-1]
    name_index = index
    index+=1
    if tokens[index][-1] == "(":
        index+=1
        while tokens[index][-1] != ")":
            current_exp = statement()
            current_exp.args, index = parse_body(index, tokens, ",", ")")
            function.args.append(current_exp)
        if sw_declared_args[function.name] != -1 and len(function.args) != sw_declared_args[function.name]:
            if len(function.args) == 1:
                parser_error(tokens[name_index], f"Function '&t' takes exactly {sw_declared_args[function.name]} argument(s) but 1 was given")
            else:
                parser_error(tokens[name_index], f"Function '&t' takes exactly {sw_declared_args[function.name]} argument(s) but {len(function.args)} were given")
                
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
    if tokens[index][-1] == "(":
        function.args, index = parse_body(index+1, tokens, ")")
        for arg in function.args:
            if arg.type == sw_type.VOID:
                parser_error(tokens[name_index], "In function declaration '&t', cannot have 'void' as input type")
        add_usr_func(function.name, function.type, tokens[name_index], len(function.args))
    else:
        parser_error(tokens[index], "Missing arguments for function '&t'")
    
    if len(tokens) <= index:
        parser_error(tokens[name_index], "Missing body for function '&t'")
    
    debug("func decl token after argument parse:", tokens[index][-1])
    block_start = index
    if tokens[index][-1] == "{":
        function.block, index = parse_block(index+1, tokens)
        if not len(function.block.args):
            parser_error(tokens[block_start], "Empty block is not allowed")
        if function.block.args[-1].kind != kind.INTRINSIC or function.block.args[-1].name != "return":
            parser_error(tokens[index-1], "Function must always end with return")
        function.block.args[-1].type = function.type
    else:
        parser_error(tokens[index], "Function body MUST be a block: {}")
    return function, index

tokens = list(lex_lines(INFILE_PATH))
debug(tokens, "\n\n")
par_statements, _ = parse_statements(0, tokens)
statements += par_statements

if not len(statements):
    parser_error((INFILE_PATH,0,2,""), "No statements found in the file, consider creating a main entry point.\n\n    - Are you happy now, Rexim?\n\n    expected:\n\n    func int main() {\n      return 0;\n    }")
if "main" not in sw_declared_funcs:
    parser_error((INFILE_PATH,0,0,""), "No main entry point found in the file, consider creating a main entry point.\n\n    expected:\n\n    func int main() {\n      return 0;\n    }")
def print_state(states: list[statement], level: int = 0):
    nlevel = level+1
    for state in states:
        debug(f"{" "*level*2}Name:", state.name)
        debug(f"{" "*level*2} -Type:", human_type[state.type])
        debug(f"{" "*level*2} -Kind:", human_kind[state.kind])
        debug(f"{" "*level*2} -Val :", state.value)
        if len(state.args):
            debug(f"{" "*level*2} -Args:")
            try:
                print_state(state.args, nlevel)
            except Exception as e:
                debug("Not printable:", e, state.args)
        if state.block:
            debug(f"{" "*level*2} -Block:")
            try:
                print_state([state.block,], nlevel)
            except Exception as e:
                debug("Not printable:", e, state.block)

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
        case kind.EXPRESSION | kind.BLOCK:
            debug("Compiling function call:", state.name)
            # out_writeln(f"; Function call: {state.name}", level)
            for arg in state.args:
                debug(f"EXP:BLK: arg.kind: {human_kind[arg.kind]}")
                arg_iota, arg_type = compile_statement(arg, level)
            return arg_iota, arg_type
        
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
            for idx, (arg_iota, arg_type) in enumerate(type_liota):
                if idx:
                    out_write(", ")
                out_write(f"{arg_type} %{arg_iota}")
            out_writeln(")")
            return iota(-1), llvm_type[available_func[state.name]]
        
        case kind.FUNC_DECL:
            debug("Compiling function declaration:", state.name)
            # out_writeln(f"; Function declaration: {state.name}", level)
            if level:
                compiler_error(state, "Function declaration cannot be nested")
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
            out_write("}\n")
            return iota(-1), llvm_type[state.type]
        
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
                    arg_iota, arg_type = compile_statement(arg, level)
                if len(state.args):
                    if arg_type != llvm_type[state.type]:
                        compiler_error(state, f"Declared as '{human_type[state.type]}' but received '{human_type[llvm_type.index(arg_type)]}'")
                    out_writeln(f"store {arg_type} %{arg_iota}, ptr %{state.name}", level)
            return iota(-1), llvm_type[state.type]
                
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
            arg_type = "-none"
            match state.subkind:
                case INTRINSIC.RET:
                    if state.type == sw_type.VOID:
                        if len(state.args):
                            compiler_error(state, "void return cannot take any argument")
                    else:
                        if len(state.args) > 1:
                            compiler_error(state, "non void return can only take 1 argument")
                        elif len(state.args) < 1:
                            compiler_error(state, "non void return must take 1 argument")
                        current_type_iota = compile_statement(state.args[0], level)

                    out_write(f"ret ", level)
                    if state.type == sw_type.VOID:
                        out_write("void ")
                        arg_type = llvm_type[sw_type.VOID]
                    else:
                        arg_iota, arg_type = current_type_iota
                        if llvm_type.index(arg_type) != state.type:
                            compiler_error(state, f"function and return types don't match: {llvm_type[state.type]} != {arg_type}")
                        out_write(f"{arg_type} %{arg_iota} ")
                        out_writeln("")
                case INTRINSIC.LLVM:
                    debug("Compiling LLVM intrinsic:", state.name)
                    if len(state.args) != 1:
                        compiler_error(state, f"Intrinsic '&t' expects one and only one argument, but {len(state.args)} were given.")
                    out_writeln(string_literals[state.args[0].name][1:-1], level)
                    string_literals.pop(state.args[0].name)
                case INTRINSIC.INCLUDE:
                    debug("Compiling INCLUDE instrinsic:", state.name)
                    if not len(state.args):
                        compiler_error(state, f"No file path provided for '&t' intrinsic")
            return iota(), arg_type

        case kind.OPERAND:
            debug("Compiling operand:", state.name)
            # out_writeln(f"; Operand: {state.name}", level)
            prev_ptr = iota(-1)-1
            prev_iota = iota(-1)
            arg_type = "i64"
            arg_iota = None
            debug("len of args:", len(state.args))
            if len(state.args):
                for arg in state.args:
                    debug(arg)
            for arg in state.args:
                arg_iota, arg_type = compile_statement(arg, level)
            if state.name == "=":
                out_writeln(f"store {arg_type} %{arg_iota}, ptr %{prev_ptr}", level)
            match state.name:
                case "+":
                    out_writeln(f"%{iota()} = add {arg_type} %{prev_iota}, %{arg_iota}", level)
                case "-":
                    out_writeln(f"%{iota()} = sub {arg_type} %{prev_iota}, %{arg_iota}", level)
                case "*":
                    out_writeln(f"%{iota()} = mul {arg_type} %{prev_iota}, %{arg_iota}", level)
                case "/":
                    out_writeln(f"%{iota()} = sdiv {arg_type} %{prev_iota}, %{arg_iota}", level)
                case "++":
                    out_writeln(f"%{iota()} = add i64 %{prev_iota}, 1", level)
                    out_writeln(f"store i64 %{iota(-1)}, ptr %{prev_ptr}", level)
                case "--":
                    out_writeln(f"%{iota()} = sub i64 %{prev_iota}, 1", level)
                    out_writeln(f"store i64 %{iota(-1)}, ptr %{prev_ptr}", level)
                case ">":
                    out_writeln(f"%{iota()} = icmp sgt {arg_type} %{prev_iota}, %{arg_iota}", level)
                    arg_type = llvm_type[sw_type.BOOL]
                case "<=":
                    out_writeln(f"%{iota()} = icmp sgt {arg_type} %{prev_iota}, %{arg_iota}", level)
                    arg_type = llvm_type[sw_type.BOOL]
                    out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                    arg_type = llvm_type[sw_type.BOOL]
                case "<":
                    out_writeln(f"%{iota()} = icmp slt {arg_type} %{prev_iota}, %{arg_iota}", level)
                    arg_type = llvm_type[sw_type.BOOL]
                case ">=":
                    out_writeln(f"%{iota()} = icmp slt {arg_type} %{prev_iota}, %{arg_iota}", level)
                    out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                    arg_type = llvm_type[sw_type.BOOL]
                case "!":
                    out_writeln(f"%{iota()} = xor {arg_type} %{arg_iota}, true", level)
                    arg_type = llvm_type[sw_type.BOOL]
                case "==":
                    out_writeln(f"%{iota()} = icmp eq {arg_type}, %{prev_iota}", level)
                    arg_type = llvm_type[sw_type.BOOL]
                case "!=":
                    out_writeln(f"%{iota()} = icmp eq {arg_type}, %{prev_iota}", level)
                    out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                    arg_type = llvm_type[sw_type.BOOL]
            debug("Operand:", state.name, "done")
            return iota(-1), arg_type

        case kind.BRANCH:
            debug("Compiling branch:", state.name)
            # out_writeln(f"; Branch: {state.name}", level)
            branch_id = iota()
            if state.name == "if":
                arg_iota, arg_type = compile_statement(state.args[0], level)
                if arg_type != sw_type.BOOL:
                    out_writeln(f"%{iota()} = icmp ne {arg_type} %{arg_iota}, 0", level)
                    out_write(f"br i1 %{iota(-1)}, label %then.{branch_id}", level)
                if len(state.args) > 1:
                    out_writeln(f", label %else.{branch_id}")
                else:
                    out_writeln(f", label %done.{branch_id}")
                out_writeln(f"then.{branch_id}:", level)
                compile_statement(state.block, nlevel)
                out_writeln(f"br label %done.{branch_id}", nlevel)
                if len(state.args) > 1:
                    out_writeln(f"else.{branch_id}:", level)
                    compile_statement(state.args[1], nlevel)
                    out_writeln(f"br label %done.{branch_id}", nlevel)
                out_writeln(f"done.{branch_id}:", level)
            elif state.name == "else":
                compile_statement(state.block, level)
            elif state.name == "while":
                out_writeln(f"br label %cond.{branch_id}", level)
                out_writeln(f"cond.{branch_id}:", level)
                arg_iota, arg_type = compile_statement(state.args[0], nlevel)
                out_writeln(f"%{iota()} = icmp ne {arg_type} %{arg_iota}, 0", nlevel)
                out_writeln(f"br i1 %{iota(-1)}, label %body.{branch_id}, label %end.{branch_id}", nlevel)
                out_writeln(f"body.{branch_id}:", level)
                compile_statement(state.block, nlevel)
                out_writeln(f"br label %cond.{branch_id}", nlevel)
                out_writeln(f"end.{branch_id}:", level)
            else:
                compiler_error(state, "Branch '&t' is not implemented yet")
            return iota(-1), arg_type
        case _:
            debug(f"SOMEHOW GOT HERE: {state.kind}")
            print_state((state,))

out_writeln(f"""; FILE: {INFILE_PATH}

declare void @printf(i8*, ...)
declare ptr @malloc(i64)
declare void @free(ptr)
declare void @exit(i64)
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

# for idx, (key, arg_type) in enumerate(sw_declared_vars.items()):
#     out_writeln(f"@{key} = global {llvm_type[arg_type]} 0")

out.close()

os.system(f"clang {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module -target x86_64-64w-mingw32")