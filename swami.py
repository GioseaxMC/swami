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
DEB_LEVEL = 0
def debug(*arguments) -> None:
    if not DEBUGGING:
        return
    print("|  "*DEB_LEVEL, end="")
    for arg in arguments:
        print(arg, end=" ")
    print()

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

def loud_call(func):
    global DEB_LEVEL;
    def wrapper(*args, **kwargs):
        global DEB_LEVEL
        debug("[CALL]:", func.__name__)
        DEB_LEVEL+=1
        ret = func(*args, **kwargs)
        DEB_LEVEL-=1
        debug("[ENDC]:", func.__name__)
        return ret
    return wrapper

@dataclass
class kind:
    FUNC_CALL = iota(1)
    FUNC_DECL = iota()
    STR_LITER = iota()
    BLOCK = iota()
    VAR_DECL = iota()
    NUM_LITER = iota()
    INTRINSIC = iota()
    VAR_REF = iota()
    OPERAND = iota()
    BRANCH = iota()
    EXPRESSION = iota()
    FUNC_EXT = iota()
    PLAIN_TYPE = iota()
    FUNC_INT = iota()
    STRUCT = iota()
    STRUCT_REF = iota()
    PTR_REF = iota()

stoppers = [";)}"]

@dataclass
class sw_type:
    PTR  = iota(1)
    INT  = iota()
    VOID = iota()
    CHAR = iota()
    BOOL  = iota()

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

human_type = [
    "ptr",
    "int",
    "void",
    "char",
    "bool",
    "//",
]

llvm_type = [
    "ptr",
    "i64",
    "void",
    "i8",
    "i1",
    "...",
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
    "function extern",
    "plain typename",
    "function intern",
    "struct",
    "struct attribute reference",
    "ptr dereferencing",

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
    CAST = iota()
    SIZEOF = iota()

human_intrinsic = [
    "return",
    "llvm",
    "include",
    "cast",
    "sizeof",
]

human_branch = [
    "if",
    "else",
    "while"
]

llvm_intrinsic = [
    "ret",
    "",
    "",
    "",
]

sw_declared_funcs = dict()
sw_declared_funcs_pevel = {
    "printf" : 0,
    "println" : 0,
    "print" : 0
}
sw_declared_funcs_args = {
    "printf" : -1,
    "println" : 1,
    "print" : 1
} # maybe for future use \ no wayy
sw_declared_vars  = dict()
sw_declared_vars_pevel  = dict()
sw_declared_v_lvl = dict()
sw_struct_info = dict()
@dataclass
class struct_info:
    names = []
    types = []
    ptrl = []

def add_usr_func(name, type, ptr_level, token, length):
    global sw_declared_funcs
    if name not in sw_declared_funcs:
        sw_declared_funcs[name] = type
        sw_declared_funcs_args[name] = length
        sw_declared_funcs_pevel[name] = ptr_level
    else:
        parser_error(token, "Redefinition of function '&t'") # this

def add_usr_var(name, type, ptr_level, token):
    global sw_declared_vars
    if name not in sw_declared_vars:
        sw_declared_vars[name] = type
        sw_declared_vars_pevel[name] = ptr_level
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
    "<=",
    "&",
    "."
]

string_literals = {}
def add_string(tokens, index):
    string_literals["str."+str(len(string_literals)+1)] = tokens[index][-1]
    return "str."+str(len(string_literals))

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
        self.ptr_level = 0
        self.subtype = -1
        self.args = []
        self.block = None
        self.value = None
        self.ogToken = None

statements: list[statement] = []

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

def parse_statement(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    current_tk = tokens[index+0][-1]
    ogToken = tokens[index]
    current_statement = statement()
    match current_tk:
        case ";"|"," :
            return None, index+1
        case "func":
            current_statement, index = parse_function_declaration(index, tokens)
        case "extern":
            current_statement, index = parse_function_external(index, tokens)
        case "intern":
            current_statement, index = parse_function_internal(index, tokens)
        case "{":
            current_statement, index = parse_block(index+1, tokens)
        case "(":
            current_statement, index = parse_expression(index, tokens)
        case "[":
            current_statement, index = parse_ptr_reference(index, tokens)
        case "struct":
            current_statement, index = parse_struct(index, tokens)
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
                    if tokenizable(current_tk):
                        parser_error(tokens[index], "'&t' is undefined")
                    else:
                        return statement(), -1;
    current_statement.ogToken = ogToken
    current_statement.lastToken = tokens[index-1]
    return current_statement, index

def parse_block(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    blocker = statement()
    blocker.kind = kind.BLOCK
    blocker.args, index = parse_body(index, tokens, "}")
    return blocker, index

@loud_call
def parse_expression(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    index+=1
    expression = statement()
    expression.kind = kind.EXPRESSION
    expression.args, index = parse_body(index, tokens, ")")
    debug(f"Expression type is: {expression.args[0].type}")
    expression.type = expression.args[0].type
    return expression, index

@loud_call
def parse_sbrackets(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    if tokens[index][-1] != "[":
        parser_error(tokens[index], "Expected '[', found '&t', instead")
    index+=1
    expression = statement()
    while tokens[index][-1] != "]":
        expression.args, index = parse_body(index, tokens, ",", "]")
    index+=1
    return expression, index

@loud_call
def parse_ptr_reference(index: int, tokens: tuple[str, int, int, str]) -> tuple[list[statement], int]:
    ptr_ref = statement()
    ptr_ref.kind = kind.PTR_REF
    current_stm, index = parse_sbrackets(index, tokens)
    if current_stm.args[0].type != sw_type.INT:
        parser_error(tokens[index], "Pointer indexing takes 1 integer as argument")
    ptr_ref.args = current_stm.args
    return ptr_ref, index

@loud_call
def parse_structattr(index: int, tokens: tuple[str, int, int, str]) -> tuple[list[statement], int]:
    name = statement()
    if tokens[index][-1] not in human_type:
        parser_error(tokens[index], "invalid typename for struct attribute")
    name.type, name.ptr_level, index = parse_typename(index, tokens)
    name.name = tokens[index][-1]
    debug(f"[ATTR]: Type idx's for struct.attr {name.name}, {rlt(name.type, name.ptr_level)}:{(name.type, name.ptr_level)}")
    if not tokenizable(name.name):
        parser_error(tokens[index], "'&t' is not a valid struct attribute name")
    index+=1
    if tokens[index][-1] != ";":
        parser_error(tokens[index-1], "Expected ';' after attribute name")
    return name, index

def parse_typename(index: int, tokens: tuple[str, int, int, str], level = 0) -> tuple[int, int, int]:
    debug("typeparsing", tokens[index][-1])
    if tokens[index][-1] not in human_type:
        if level:
            parser_error(tokens[index-1], "'&t' expected a typename, (use void to specify a generic ptr).")
        else:
            parser_error(tokens[index], "'&t' is not a valid type.")
    type = human_type.index(tokens[index][-1])
    index+=1
    if type == sw_type.VOID and level:
        return sw_type.CHAR, level, index
    if type == sw_type.PTR:
        type, level, index = parse_typename(index, tokens, level+1)
        return type, level, index
    return type, level, index


@loud_call
def parse_struct(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    index+=1
    struct = statement()
    struct.name = tokens[index][-1]
    if not tokenizable(struct.name):
        parser_error(tokens[index], "Token '&t' is not fit to be a struct name.")
    if struct.name in sw_builtins or struct.name in (human_intrinsic+human_branch+human_type):
        parser_error(tokens[index], "Token '&t' is a reserved keyword and cannot be a struct name.")
    human_type.append(struct.name)
    llvm_type.append(f"%struct.{struct.name}")
    # add_usr_var(struct.name, struct.type, tokens[index]) # TODO: WHY IS THIS HERE
    struct.kind = kind.STRUCT
    index+=1
    if tokens[index][-1] == "{":
        index+=1
        while tokens[index][-1] != "}":
            current_name, index = parse_structattr(index, tokens)
            struct.args.append(current_name)
            index+=1
    else:
        parser_error(tokens[index], "Expected struct body")
    str_info = struct_info()
    sw_struct_info[f"%struct.{struct.name}"] = str_info
    sw_struct_info[f"%struct.{struct.name}"].names = [x.name for x in struct.args]
    sw_struct_info[f"%struct.{struct.name}"].types = [x.type for x in struct.args]
    sw_struct_info[f"%struct.{struct.name}"].ptrl = [x.ptr_level for x in struct.args]
    return struct, index+1
    

@loud_call
def parse_body(index: int, tokens: tuple[str, int, int, str], stop_at, safefail_on="") -> tuple[list[statement], int]:
    debug(f"[BLOCK]: starting with ({stop_at})")
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
    global statements, current_func_type
    intrinsic = statement()
    intrinsic.name = tokens[index][-1]
    intrinsic.kind = kind.INTRINSIC
    intrinsic.subkind = human_intrinsic.index(tokens[index][-1])
    intrinsic.block = statement()
    if tokens[index][-1] == "include":
        index+=1
        intrinsic.args, index = parse_body(index, tokens, ";")
        for arg in intrinsic.args:
            included_path = string_literals[arg.name][1:-1]
            inc_tokens = list(lex_lines(included_path))
            debug(inc_tokens, "\n\n")
            inc_statements, _ = parse_statements(0, inc_tokens)
        statements += inc_statements

    elif tokens[index][-1] == "sizeof":
        index+=1
        if tokens[index][-1] == "(":
            index+=1
            intrinsic.type, intrinsic.ptr_level, index = parse_typename(index, tokens)
        else:
            parser_error(tokens[index-1], "Expected '(' after a call to 'cast'")
        index+=1

    elif tokens[index][-1] == "cast": #===================
        index+=1
        if tokens[index][-1] == "(":
            index+=1
            intrinsic.type, intrinsic.ptr_level, index = parse_typename(index, tokens)
        else:
            parser_error(tokens[index-1], "Expected '(' after a call to 'cast'")
        if tokens[index][-1] == ",":
            index+=1
            intrinsic.args, index = parse_body(index, tokens, ")")
        else:
            parser_error(tokens[index-1], "Expected ',' with an expression to evaluate after 'cast(<type>'")

    else:
        if intrinsic.subkind == INTRINSIC.RET:
            intrinsic.type, intrinsic.ptr_level = current_func_type
        index+=1
        intrinsic.args, index = parse_body(index, tokens, ";")
    return intrinsic, index


@loud_call
def parse_num_literal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    number = statement()
    number.kind = kind.NUM_LITER
    number.type = sw_type.INT
    number.value = tokens[index][-1]
    return number, index+1

@loud_call
def parse_str_literal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    current_stm = statement()
    current_stm.name = add_string(tokens, index)
    current_stm.kind = kind.STR_LITER
    current_stm.type = sw_type.CHAR
    current_stm.ptr_level = 1
    return current_stm, index+1

@loud_call
def parse_var_decl(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    variable = statement()
    variable.type, variable.ptr_level, index = parse_typename(index, tokens) # is always be true
    variable.kind = kind.VAR_DECL
    if variable.type == sw_type.VOID and not variable.ptr_level:
        if tokens[index+1][-1].isalnum():
            parser_error(tokens[index], "type void cannot describe a value")
    else:
        variable.name = tokens[index][-1]
        debug(f"VARIABLE: name: {variable.name} type: {llvm_type[variable.type] + "*"*variable.ptr_level}")
        if not tokenizable(variable.name):
            parser_error(tokens[index], "Token '&t' is not fit to be a variable name.")
        if variable.name in sw_builtins or variable.name in (human_intrinsic+human_branch+human_type):
            parser_error(tokens[index], "Token '&t' is a reserved keyword and cannot be a variable name.")
        add_usr_var(variable.name, variable.type, variable.ptr_level, tokens[index])
        index+=1
        if tokens[index][-1] == "=":
            debug("[VARDECL]: Detected equal sign, parsing with ;")
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
    variable.ptr_level = sw_declared_vars_pevel[tokens[index][-1]]
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
    elif operand.name in "!&":
        current_stm, index = parse_statement(index, tokens)
        operand.args.append(current_stm)
    elif operand.name == ".":
        current_stm = statement()
        current_stm.name = tokens[index][-1]
        current_stm.kind = kind.STRUCT_REF
        operand.args.append(current_stm)
        index+=1
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
        if sw_declared_funcs_args[function.name] != -1 and len(function.args) != sw_declared_funcs_args[function.name]:
            if len(function.args) == 1:
                parser_error(tokens[name_index], f"Function '&t' takes exactly {sw_declared_funcs_args[function.name]} argument(s) but 1 was given")
            else:
                parser_error(tokens[name_index], f"Function '&t' takes exactly {sw_declared_funcs_args[function.name]} argument(s) but {len(function.args)} were given")
                
    else:
        parser_error(tokens[index], "Missing arguments for function '&t'")
    return function, index+1

@loud_call
def parse_function_external(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    index+=1
    function = statement()
    function.kind = kind.FUNC_EXT
    if tokens[index][-1] not in human_type:
        parser_error(tokens[index], "invalid typename for function")
    function.type, function.ptr_level, index = parse_typename(index, tokens)
    function.name = tokens[index][-1]
    name_index = index
    index+=1
    if tokens[index][-1] == "(":
        index+=1
        while tokens[index][-1] != ")":
            if tokens[index][-1] == ",":
                index+=1    
            arg_stm = statement()
            arg_stm.kind = kind.PLAIN_TYPE
            arg_stm.type, arg_stm.ptr_level, index = parse_typename(index, tokens)
            debug("Parsed:", tokens[index][-1])
            function.args.append(arg_stm)
        for arg in function.args:
            if arg.type == sw_type.VOID:
                parser_error(tokens[name_index], "In function extern '&t': cannot have 'void' as input type")
        if function.args[-1].type == 6:
            arg_len = -1
        else:
            arg_len = len(function.args)
        add_usr_func(function.name, function.type, function.ptr_level, tokens[name_index], arg_len)
    else:
        parser_error(tokens[index], "Missing arguments for function '&t'")
    return function, index+1

@loud_call
def parse_function_internal(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    index+=1
    function = statement()
    function.kind = kind.FUNC_INT
    function.type, function.ptr_level, index = parse_typename(index, tokens)
    function.name = tokens[index][-1]
    name_index = index
    index+=1
    if tokens[index][-1] == "(":
        index+=1
        while tokens[index][-1] != ")":
            if tokens[index][-1] != ",":
                arg_stm = statement()
                arg_stm.kind = kind.PLAIN_TYPE
                if tokens[index][-1] not in human_type:
                    parser_error(tokens[index], "invalid type for function internation '&t'")
                arg_stm.type, arg_stm.ptr_level, index = parse_typename(index, tokens)
                debug(".NEXT UP:", tokens[index][-1])
                function.args.append(arg_stm)
            else:
                index+=1
        for arg in function.args:
            if arg.type == sw_type.VOID:
                parser_error(tokens[name_index], "In function intern '&t': cannot have 'void' as input type")
        if function.args[-1].type == 6:
            arg_len = -1
        else:
            arg_len = len(function.args)
        add_usr_func(function.name, function.type, function.ptr_level, tokens[name_index], arg_len)
    else:
        parser_error(tokens[name_index], "Missing arguments for internal function '&t'")
    return function, index+1

current_func_type = (0, 0)
@loud_call
def parse_function_declaration(index: int, tokens: tuple[str, int, int, str]) -> tuple[statement, int]:
    global current_func_type
    index+=1
    function = statement()
    function.kind = kind.FUNC_DECL
    if tokens[index][-1] not in human_type:
        parser_error(tokens[index], "Invalid type name")
    function.type, function.ptr_level, index = parse_typename(index, tokens)
    current_func_type = function.type, function.ptr_level
    function.name = tokens[index][-1]
    name_index = index
    index+=1
    if tokens[index][-1] == "(":
        function.args, index = parse_body(index+1, tokens, ")")
        for arg in function.args:
            if arg.type == sw_type.VOID:
                parser_error(tokens[name_index], "In function declaration '&t', cannot have 'void' as input type")
        add_usr_func(function.name, function.type, function.ptr_level, tokens[name_index], len(function.args))
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
        # if DEBUGGING:
        #     print_state(function.block.args)
        if function.block.args[-1].kind != kind.INTRINSIC: #or function.block.args[-1].name != "return":
            debug(human_kind[function.block.args[-1].kind])
            parser_error(tokens[index-1], "Function must always end with return")
        function.block.args[-1].type = function.type
        function.block.args[-1].ptr_level = function.ptr_level
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

compile_stack = []
compilation_returned = 0
def stacked_call(func):
    def wrapper(*args, **kwargs):
        ret = func(*args, *kwargs)
        compile_stack.append(ret)
        return ret
    return wrapper

def cast(arg_iota, arg_type, arg_ptrl, state_type, state_ptrl, level):
    typecmp = bool(arg_ptrl) - bool(state_ptrl) # > 0 
    isptr = arg_ptrl or state_ptrl
    bothp = arg_ptrl and state_ptrl
    if (arg_type, arg_ptrl) == (state_type, state_ptrl):
        return iota(-1), state_type, state_ptrl
    if bothp:
        out_writeln(f"%{iota()} = bitcast {rlt(arg_type, arg_ptrl)} %{arg_iota} to {rlt(state_type, state_ptrl)}", level)
    elif isptr:
        if typecmp > 0:
            out_writeln(f"%{iota()} = ptrtoint {rlt(arg_type, arg_ptrl)} %{arg_iota} to {rlt(state_type, state_ptrl)}", level)
        else:
            out_writeln(f"%{iota()} = inttoptr {rlt(arg_type, arg_ptrl)} %{arg_iota} to {rlt(state_type, state_ptrl)}", level)
    else:
        if state_type == sw_type.BOOL:
            out_writeln(f"%{iota()} = icmp ne {rlt(arg_type, arg_ptrl)} %{arg_iota}, 0", level)
        else:
            if sizeof(state_type, state_ptrl) > sizeof(arg_type, arg_ptrl):
                out_writeln(f"%{iota()} = zext {rlt(arg_type, arg_ptrl)} %{arg_iota} to {rlt(state_type, state_ptrl)}", level)
            elif sizeof(state_type, state_ptrl) < sizeof(arg_type, arg_ptrl):
                out_writeln(f"%{iota()} = trunc {rlt(arg_type, arg_ptrl)} %{arg_iota} to {rlt(state_type, state_ptrl)}", level)
            else:
                out_writeln(f"%{iota()} = bitcast {rlt(arg_type, arg_ptrl)} %{arg_iota} to {rlt(state_type, state_ptrl)}", level)
    return iota(-1), state_type, state_ptrl #iota -1 : casted val


@stacked_call
@loud_call
def compile_statement(state, level: int = 0) -> tuple[int, int, int]:
    # out_writeln(f"; {human_kind[state.kind]}")
    global compilation_returned
    compilation_returned = 0
    nlevel = level+1
    type_liota = []
    prev_ptr = iota(-1)-1
    current_type_iota = None
    prev_iota = iota(-1)
    prev_type = 0
    prev_ptrl = 0
    if len(compile_stack):
        debug("Compile stack not empty")
        prev_iota, prev_type, prev_ptrl = compile_stack[-1]
    match state.kind:
        case kind.EXPRESSION | kind.BLOCK:
            debug("Compiling function call:", state.name)
            # out_writeln(f"; Function call: {state.name}", level)
            for arg in state.args:
                debug(f"EXP:BLK: arg.kind: {human_kind[arg.kind]}")
                arg_iota, arg_type, arg_ptrl = compile_statement(arg, level)
            return arg_iota, arg_type, arg_ptrl
        
        case kind.PTR_REF:
            debug("Compiling pointer dereferencing")
            for arg in state.args:
                compile_statement(arg, level)
            out_writeln(f"%{iota()} = getelementptr {rlt(prev_type, prev_ptrl-1)}, {rlt(prev_type, prev_ptrl)} %{prev_iota}, i64 %{iota(-1)-1}", level)
            out_writeln(f"%{iota()} = load {rlt(prev_type, prev_ptrl-1)}, {rlt(prev_type, prev_ptrl)} %{iota(-1)-1}", level)
            return iota(-1), prev_type, prev_ptrl-1
        
        case kind.STRUCT_REF:
            reference_idx = sw_struct_info[llvm_type[prev_type]].names.index(state.name) # struct name types index
            ref_type = sw_struct_info[llvm_type[prev_type]].types[reference_idx] # struct attr type
            ref_ptrl = sw_struct_info[llvm_type[prev_type]].ptrl[reference_idx] # struct attr type
            ref_typename = llvm_type[ref_type] # struct attr typename
            out_writeln(f"%{iota()} = getelementptr {rlt(prev_type, prev_ptrl)}, ptr %{prev_ptr}, i32 0, i32 {reference_idx}", level)
            out_writeln(f"%{iota()} = load {rlt(ref_type, ref_ptrl)}, ptr %{iota(-1)-1}", level)
            debug(F"[STRUCTREF]: {iota(-1), ref_type, ref_ptrl}")
            return iota(-1), ref_type, ref_ptrl
        
        case kind.STRUCT:
            if level:
                compiler_error(state, "struct definition must be global")
            debug("Compiling struct", state.name)
            out_write(f"%struct.{state.name} = type {{ ")
            for idx, arg in enumerate(state.args):
                if idx:
                    out_write(", ")
                out_write(rlt(arg.type, arg.ptr_level))
            out_writeln(" }\n")
            return compile_stack[-1]

        case kind.FUNC_CALL:
            debug("Compiling function call:", state.name)
            # out_writeln(f"; Function call: {state.name}", level)
            for argstate in state.args:
                for arg in argstate.args:
                    current_type_iota = compile_statement(arg, level)
                    arg_iota, arg_type, arg_ptrl = current_type_iota
                    debug(f"[COMPILATION]: type in func call: {rlt(arg_type, arg_ptrl)}")
                debug(f"[COMPILATION]: next up ->")
                type_liota.append(current_type_iota)
            if available_func[state.name] == sw_type.VOID:
                out_write(f"call void @{state.name}(", level)
            else:
                out_write(f"%{iota()} = call {rlt(available_func[state.name], sw_declared_funcs_pevel[state.name])} @{state.name}(", level)
            for idx, (arg_iota, arg_type, arg_ptrl) in enumerate(type_liota):
                if idx:
                    out_write(", ")
                out_write(f"{rlt(arg_type, arg_ptrl)} %{arg_iota}")
            out_writeln(")")
            return iota(-1), available_func[state.name], sw_declared_funcs_pevel[state.name]
        
        case kind.FUNC_EXT:
            debug("Compiling function external:", state.name)
            # out_writeln(f"; Function declaration: {state.name}", level)
            if level:
                compiler_error(state, "Function externing cannot be nested")
            out_write(f"declare {rlt(state.type, state.ptr_level)} @{state.name}(")
            for idx, arg in enumerate(state.args):
                out_write(f"{rlt(arg.type, arg.ptr_level)}")
                if idx+1 != len(state.args):
                    out_write(", ")
            len_args = len(state.args)
            out_writeln(")")
            return compile_stack[-1]

        case kind.FUNC_DECL:
            debug("Compiling function declaration:", state.name)
            # out_writeln(f"; Function declaration: {state.name}", level)
            if level:
                compiler_error(state, "Function declaration cannot be nested")
            out_write(f"define {rlt(state.type, state.ptr_level)} @{state.name}(")
            for idx, arg in enumerate(state.args):
                out_write(f"{rlt(arg.type, arg.ptr_level)} %{iota()}")
                if idx+1 != len(state.args):
                    out_write(", ")
            len_args = len(state.args)
            out_write(") {\n")
            for idx, arg in enumerate(state.args):
                out_writeln(f"%{arg.name} = alloca {rlt(arg.type, arg.ptr_level)}", nlevel)
                out_writeln(f"store {rlt(arg.type, arg.ptr_level)} %{iota()-len_args}, ptr %{arg.name}", nlevel)
            for stm in state.block.args:
                compile_statement(stm, nlevel)
            # out_writeln("ret i64 0", nlevel)
            out_writeln("\n}\n")
            return iota(-1), state.type, state.ptr_level
        
        case kind.NUM_LITER:
            debug("Compiling int literal:", state.value)
            # out_writeln(f"; Int literal: {state.value}", level)
            out_writeln(f"%{iota()} = add i64 {state.value}, 0", level)
            return iota(-1), sw_type.INT, 0
        
        case kind.STR_LITER:
            debug("Compiling string literal:", state.name)
            # out_writeln(f"; Str literal: {state.name}", level)
            out_writeln(f"%{iota()} = load ptr, ptr @{state.name}.ptr", level)
            return iota(-1), sw_type.CHAR, 1
        
        case kind.VAR_DECL:
            debug("Compiling variable declaration:", state.name)
            # out_writeln(f"; Variable declaration: {state.name}", level)
            sw_declared_v_lvl[state.name] = level
            if level == 0:
                if state.value:
                    out_writeln(f"@{state.name} = global {rlt(state.type, state.ptr_level)} {state.value}")
                else:
                    if state.ptr_level:
                        out_writeln(f"@{state.name} = global {rlt(state.type, state.ptr_level)} null")
                    else:
                        out_writeln(f"@{state.name} = global {rlt(state.type, state.ptr_level)} 0")
            else:
                out_writeln(f"%{state.name} = alloca {rlt(state.type, state.ptr_level)}", level)
                for arg in state.args:
                    arg_iota, arg_type, arg_ptrl = compile_statement(arg, level)
                if len(state.args):
                    if (arg_type, arg_ptrl) != (state.type, state.ptr_level):
                        compiler_error(state, f"Declared as '{"ptr "*state.ptr_level}{human_type[state.type]}' but received '{"ptr "*arg_ptrl}{human_type[arg_type]}'")
                    out_writeln(f"store {rlt(arg_type, arg_ptrl)} %{arg_iota}, ptr %{state.name}", level)
            return iota(-1), state.type, state.ptr_level
                
        case kind.VAR_REF:
            debug("Compiling variable reference:", state.name)
            # out_writeln(f"; Variable reference: {state.name}", level)
            if sw_declared_v_lvl.get(state.name) == 0:
                out_writeln(f"%{iota()} = bitcast ptr @{state.name} to ptr", level)
                out_writeln(f"%{iota()} = load {rlt(sw_declared_vars[state.name], sw_declared_vars_pevel[state.name])}, ptr %{iota(-1)-1}", level)
            else:
                out_writeln(f"%{iota()} = bitcast ptr %{state.name} to ptr", level)
                out_writeln(f"%{iota()} = load {rlt(sw_declared_vars[state.name], sw_declared_vars_pevel[state.name])}, ptr %{iota(-1)-1}", level)
            return iota(-1), sw_declared_vars[state.name], sw_declared_vars_pevel[state.name]
        
        case kind.INTRINSIC:
            arg_type, arg_ptrl = 0, 0
            debug("Compiling intrinsic:", state.name)
            # out_writeln(f"; Intrinsic: {state.name}", level)
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
                        arg_type = sw_type.VOID
                    else:
                        arg_iota, arg_type, arg_ptrl = current_type_iota
                        if (arg_type, arg_ptrl) != (state.type, state.ptr_level):
                            compiler_error(state, f"function and return types don't match: {hlt(state.type, state.ptr_level)} != {hlt(arg_type, arg_ptrl)}")
                        out_write(f"{rlt(arg_type, arg_ptrl)} %{arg_iota} ")
                        out_writeln("")
                    compilation_returned = 1
                case INTRINSIC.CAST:
                    debug("compiling CAST intrinsic:", state.name)
                    for arg in state.args:
                        arg_iota, arg_type, arg_ptrl = compile_statement(arg, level)
                    return cast(arg_iota, arg_type, arg_ptrl, state.type, state.ptr_level, level)
                case INTRINSIC.SIZEOF:
                    debug("compiling sizeof intrinsic:", state.name)
                    out_writeln(f"%{iota()} = getelementptr {rlt(state.type, state.ptr_level)}, {rlt(state.type, state.ptr_level+1)} null, i64 1", level)
                    out_writeln(f"%{iota()} = ptrtoint {rlt(state.type, state.ptr_level+1)} %{iota(-1)-1} to i64", level)
                    arg_type, arg_ptrl = sw_type.INT, 0
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
            return iota(-1), arg_type, arg_ptrl

        case kind.OPERAND:
            debug("Compiling operand:", state.name, "FROM", (prev_type, prev_ptrl))
            # out_writeln(f"; Operand: {state.name}", level)
            arg_iota, arg_type, arg_ptrl = compile_stack[-1]
            chsn_type, chsn_ptrl = arg_type, arg_ptrl
            state.type, state.ptr_level = prev_type, prev_ptrl
            debug("len of args:", len(state.args))
            if len(state.args):
                for arg in state.args:
                    debug(arg)
            for arg in state.args:
                arg_iota, arg_type, arg_ptrl = compile_statement(arg, level)
            if state.name == "!":
                if arg_ptrl:
                    niota, ntype, nptrl = cast(arg_iota, arg_type, arg_ptrl, sw_type.INT, 0, level)
                out_writeln(f"%{iota()} = icmp ne {rlt(ntype, nptrl)} %{niota}, 0", level)
                out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                return iota(-1), sw_type.BOOL, 0
            if state.name == "&":
                out_writeln(f"%{iota()} = bitcast ptr %{arg_iota-1} to ptr", level)
                return iota(-1), arg_type, arg_ptrl+1
            if state.name == ".":
                return arg_iota, arg_type, arg_ptrl
            if state.name == "=":
                debug(f"ASSIGNING: {(arg_type, arg_ptrl)} TO {(prev_type, prev_ptrl)}")
                if rlt(prev_type, prev_ptrl) == rlt(arg_type, arg_ptrl):
                    out_writeln(f"store {rlt(arg_type, arg_ptrl)} %{arg_iota}, {rlt(prev_type, prev_ptrl+1)} %{prev_ptr}", level)
                else:
                    compiler_error(state, f"Types don't match: {human_type[prev_type]+"*"*prev_ptrl} != {human_type[arg_type]+"*"*arg_ptrl}")
            nprev_iota = prev_iota
            narg_iota, chsn_type, chsn_ptrl = cast(arg_iota, arg_type, arg_ptrl, state.type, state.ptr_level, level)
            match state.name:
                case "+":
                    out_writeln(f"%{iota()} = add {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                case "-":
                    out_writeln(f"%{iota()} = sub {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                case "*":
                    out_writeln(f"%{iota()} = mul {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                case "/":
                    out_writeln(f"%{iota()} = sdiv {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                case "++":
                    out_writeln(f"%{iota()} = add {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, 1", level)
                    out_writeln(f"store {rlt(chsn_type, chsn_ptrl)} %{iota(-1)}, ptr %{prev_ptr}", level)
                case "--":
                    out_writeln(f"%{iota()} = sub {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, 1", level)
                    out_writeln(f"store {rlt(chsn_type, chsn_ptrl)} %{iota(-1)}, ptr %{prev_ptr}", level)
                case ">":
                    out_writeln(f"%{iota()} = icmp sgt {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                    chsn_type, chsn_ptrl = sw_type.BOOL, 0
                case "<=":
                    out_writeln(f"%{iota()} = icmp sgt {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                    out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                    chsn_type, chsn_ptrl = sw_type.BOOL, 0
                case "<":
                    out_writeln(f"%{iota()} = icmp slt {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                    chsn_type, chsn_ptrl = sw_type.BOOL, 0
                case ">=":
                    out_writeln(f"%{iota()} = icmp slt {rlt(chsn_type, chsn_ptrl)} %{nprev_iota}, %{narg_iota}", level)
                    out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                    chsn_type, chsn_ptrl = sw_type.BOOL, 0
                case "==":
                    out_writeln(f"%{iota()} = icmp eq {rlt(chsn_type, chsn_ptrl)} %{narg_iota}, %{iota(-1)-1}", level)
                    chsn_type, chsn_ptrl = sw_type.BOOL, 0
                case "!=":
                    out_writeln(f"%{iota()} = icmp eq {rlt(chsn_type, chsn_ptrl)} %{narg_iota}, %{iota(-1)-1}", level)
                    out_writeln(f"%{iota()} = xor i1 %{iota(-1)-1}, true", level)
                    chsn_type, chsn_ptrl = sw_type.BOOL, 0
            debug("Operand:", state.name, "done")
            return iota(-1), chsn_type, chsn_ptrl

        case kind.BRANCH:
            debug("Compiling branch:", state.name)
            # out_writeln(f"; Branch: {state.name}", level)
            branch_id = iota()
            if state.name == "if":
                arg_iota, arg_type, arg_ptrl = compile_statement(state.args[0], level)
                if compilation_returned:
                    compiler_error(state, "Cannot return inside 'if' condition")
                if arg_type != sw_type.BOOL:
                    if arg_ptrl:
                        niota, ntype, nptrl = cast(arg_iota, arg_type, arg_ptrl, sw_type.INT, 0, level)
                        out_writeln(f"%{iota()} = icmp ne {rlt(ntype, nptrl)} %{niota}, 0", level)
                    else:
                        out_writeln(f"%{iota()} = icmp ne {rlt(arg_type, arg_ptrl)} %{arg_iota}, 0", level)
                out_write(f"br i1 %{iota(-1)}, label %then.{branch_id}", level)
                if len(state.args) > 1:
                    out_writeln(f", label %else.{branch_id}")
                else:
                    out_writeln(f", label %done.{branch_id}")
                out_writeln(f"then.{branch_id}:", level)
                compile_statement(state.block, nlevel)
                if not compilation_returned:
                    out_writeln(f"br label %done.{branch_id}", nlevel)
                if len(state.args) > 1:
                    out_writeln(f"else.{branch_id}:", level)
                    compile_statement(state.args[1], nlevel)
                    if not compilation_returned:
                        out_writeln(f"br label %done.{branch_id}", nlevel)
                out_writeln(f"done.{branch_id}:", level)
            elif state.name == "else":
                compile_statement(state.block, level)
            elif state.name == "while":
                out_writeln(f"br label %cond.{branch_id}", level)
                out_writeln(f"cond.{branch_id}:", level)
                arg_iota, arg_type, arg_ptrl = compile_statement(state.args[0], nlevel)
                if not compilation_returned:
                    out_writeln(f"%{iota()} = icmp ne {rlt(arg_type, arg_ptrl)} %{arg_iota}, 0", nlevel)
                out_writeln(f"br i1 %{iota(-1)}, label %body.{branch_id}, label %end.{branch_id}", nlevel)
                out_writeln(f"body.{branch_id}:", level)
                compile_statement(state.block, nlevel)
                if not compilation_returned:
                    out_writeln(f"br label %cond.{branch_id}", nlevel)
                out_writeln(f"end.{branch_id}:", level)
            else:
                compiler_error(state, "Branch '&t' is not implemented yet")
            return iota(-1), arg_type, arg_ptrl
        case kind.FUNC_INT:
            ...
        case _:
            debug(f"SOMEHOW GOT HERE: {state.kind}")
            print_state((state,))
    return prev_iota, prev_type, prev_ptrl

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

debug("[COMPILATION] : Finished")

debug(f"{llvm_type}")

os.system(f"clang {OUTFILE_PATH} -o {OUTFILE_PATH.removesuffix('.ll')} -Wno-override-module -target x86_64-64w-mingw32")