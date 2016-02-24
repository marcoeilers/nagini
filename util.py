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
