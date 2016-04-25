import ast

from typing import TypeVar, List, Tuple, Optional, Dict, Any


T = TypeVar('T')
V = TypeVar('V')


def unzip(pairs: List[Tuple[T, V]]) -> Tuple[List[T], List[V]]:
    """
    Unzips a list of pairs into two lists
    """
    vars_and_body = [list(t) for t in zip(*pairs)]
    vars = vars_and_body[0]
    body = vars_and_body[1]
    return vars, body


def flatten(lists: List[List[T]]) -> List[T]:
    """
    Flattens a list of lists into a flat list
    """
    return [item for sublist in lists for item in sublist]


class UnsupportedException(Exception):
    """
    Exception that is thrown when attempting to translate a Python element not
    currently supported
    """

    def __init__(self, astElement: ast.AST, desc=""):
        ex_str = str(astElement)
        if desc:
            ex_str += ": " + desc
        super().__init__(ex_str)


class InvalidProgramException(Exception):
    """
    Signals that the input program is invalid and cannot be translated
    """

    def __init__(self, node: ast.AST, code: str, message: str = None):
        self.node = node
        self.code = code
        self.message = message


def get_func_name(stmt: ast.AST) -> Optional[str]:
    """
    Checks if stmt is a function call and returns its name if it is, None
    otherwise.
    """
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
    elif isinstance(stmt, ast.Call):
        call = stmt
    else:
        return None
    if isinstance(call.func, ast.Name):
        return call.func.id
    elif isinstance(call.func, ast.Attribute):
        return call.func.attr
    else:
        raise UnsupportedException(stmt)


def contains_stmt(container: Any, contained: ast.AST) -> bool:
    """
    Checks if 'contained' is a part of the partial AST
    whose root is 'container'.
    """
    if container is contained:
        return True
    if isinstance(container, list):
        for stmt in container:
            if contains_stmt(stmt, contained):
                return True
        return False
    elif isinstance(container, ast.AST):
        for field in container._fields:
            if contains_stmt(getattr(container, field), contained):
                return True
        return False
    else:
        return False


def get_surrounding_try_blocks(try_blocks: List['PythonTryBlock'],
                               stmt: ast.AST) -> List['PythonTryBlock']:
    """
    Finds the try blocks in try_blocks that protect the statement stmt.
    """
    def rank(b: 'PythonTryBlock', blocks: List['PythonTryBlock']) -> int:
        result = 0
        for b2 in blocks:
            if contains_stmt(b2.protected_region, b.node):
                result += 1
        return -result
    tb = try_blocks
    blocks = [b for b in tb if contains_stmt(b.protected_region, stmt)]
    inner_to_outer = sorted(blocks,key=lambda b: rank(b, blocks))
    return inner_to_outer


def is_two_arg_super_call(node: ast.Call, ctx) -> bool:
    """
    Checks if a super() call with two arguments is valid:
    first arg must be a class, second a reference to self.
    """
    return (isinstance(node.args[0], ast.Name) and
        (node.args[0].id in ctx.program.classes) and
        isinstance(node.args[1], ast.Name) and
        (node.args[1].id == next(iter(ctx.current_function.args))))


def get_all_fields(cls: 'PythonClass') -> List['silver.ast.Field']:
    """
    Returns a list of fields defined in the given class or its superclasses.
    """
    accs = []
    fields = []
    while cls is not None:
        for fieldname in cls.fields:
            field = cls.fields[fieldname]
            if field.inherited is None:
                fields.append(field.sil_field)
        cls = cls.superclass
    return fields
