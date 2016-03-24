import ast

from typing import TypeVar, List, Tuple, Optional, Dict


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

    def __init__(self, astElement: ast.AST):
        super().__init__(str(astElement))


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
