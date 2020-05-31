"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import astunparse

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
)


T = TypeVar('T')
V = TypeVar('V')


def flatten(lists: List[List[T]]) -> List[T]:
    """
    Flattens a list of lists into a flat list
    """
    return [item for sublist in lists for item in sublist]


def flatten_dict(dicts: List[Dict[T, List[V]]],
                 defaults: List[T]=[]) -> Dict[T, List[V]]:
    """
    Flattens a dict of lists, i.e., concatenates all lists for the same keys.
    """
    result = {}
    for key in defaults:
        result[key] = []
    for d in dicts:
        for key, value in d.items():
            if key in result:
                result[key].extend(value)
            else:
                result[key] = value
    return result


class UnsupportedException(Exception):
    """
    Exception that is thrown when attempting to translate a Python element not
    currently supported
    """

    def __init__(self, ast_element: ast.AST, desc=""):
        self.node = ast_element
        super().__init__(desc)


class InvalidProgramException(Exception):
    """
    Signals that the input program is invalid and cannot be translated
    """

    def __init__(self, node: ast.AST, code: str, message: str = None):
        self.node = node
        self.code = code
        self.message = message


class ConsistencyException(Exception):
    """
    Exception reporting that the translated AST has a consistency error
    """

    def __init__(self, message: str = None) -> None:
        self.message = message


class AssignCollector(ast.NodeVisitor):
    """
    Collects all assignment targets within a given (partial) AST.
    """
    def __init__(self):
        self.assigned_vars = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._track_assign(target)

    def _track_assign(self, target: ast.AST) -> None:
        if isinstance(target, ast.Tuple):
            actual_targets = target.elts
        else:
            actual_targets = [target]
        for actual in actual_targets:
            if isinstance(actual, ast.Name):
                self.assigned_vars[actual.id] = actual

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._track_assign(node.target)


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


def get_column(node: ast.AST) -> Optional[int]:
    return node.col_offset if hasattr(node, 'col_offset') else None


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


def is_invariant(stmt: ast.AST) -> bool:
    return get_func_name(stmt) == 'Invariant'


def is_pre(stmt: ast.AST) -> bool:
    return get_func_name(stmt) == 'Requires'


def is_post(stmt: ast.AST) -> bool:
    return get_func_name(stmt) == 'Ensures'


def is_exception_decl(stmt: ast.AST) -> bool:
    return get_func_name(stmt) == 'Exsures'


def is_docstring(stmt: ast.AST) -> bool:
    """Return True if statement is a docstring."""
    if (isinstance(stmt, ast.Expr) and
            isinstance(stmt.value, ast.Str)):
        return True
    else:
        return False


def is_io_existential(stmt: ast.AST) -> bool:
    """Return True if statement is a definition of IOExists."""
    if (isinstance(stmt, ast.Expr) and
            isinstance(stmt.value, ast.Call) and
            isinstance(stmt.value.func, ast.Call) and
            isinstance(stmt.value.func.func, ast.Name) and
            stmt.value.func.func.id.startswith('IOExists')):
        return True
    else:
        return False


def get_body_indices(statements: List[ast.AST]) -> Tuple[int, int]:
    """
    Returns the index of the first statement that is not a method
    or loop contract and the index after the last statement that is not a postcondition.

    .. note::

        In the case when a method has only a contract, both returned
        indices are equal to ``len(statements)``.
    """
    start_index = 0
    try:
        while is_docstring(statements[start_index]):
            start_index += 1
        while isinstance(statements[start_index], ast.Global):
            start_index += 1
        while is_io_existential(statements[start_index]):
            start_index += 1
        while is_invariant(statements[start_index]):
            start_index += 1
        while is_pre(statements[start_index]):
            start_index += 1
        while is_post(statements[start_index]):
            start_index += 1
        while is_exception_decl(statements[start_index]):
            start_index += 1
    except IndexError:
        # This exception means that the method/loop has only a contract.
        pass
    end_index = len(statements)
    if start_index != end_index:
        while end_index > 0 and is_post(statements[end_index - 1]):
            end_index -= 1
    return start_index, end_index


def find_loop_for_previous(node: ast.AST, name: str) -> ast.For:
    """
    In a for loop like::

        for x in xs:

    ``Previous(x)`` refers to the objects processed in previous iterations.
    Given the Previous-call-node, this function returns the for loop to whose
    previous iterations the node refers.
    """
    if isinstance(node, ast.For):
        if isinstance(node.target, ast.Name):
            if node.target.id == name:
                return node
        elif (isinstance(node.target, ast.Tuple) and node.target.elts and
                  isinstance(node.target.elts[0], ast.Name)):
            if node.target.elts[0].id == name:
                return node
    if not hasattr(node, '_parent') or not node._parent:
        return None
    return find_loop_for_previous(node._parent, name)


def get_parent_of_type(node: ast.AST, typ: type) -> ast.AST:
    parent = node._parent
    while not isinstance(parent, ast.Module):
        if isinstance(parent, typ):
            return parent
        parent = parent._parent
    return None


def join_expressions(operator: Callable[[T, T], T],
                     expressions: List[T]) -> T:
    """
    Joins expressions with ``operator``.

    This function joins expressions backwards (the last two expressions
    are most nested) in order to avoid Silicon issue
    `241 <https://bitbucket.org/viperproject/silicon/issues/241>`_.
    """
    first = expressions[-1]

    def new_op(first, second, third):
        return operator(second, third)
    return join_three_expressions(new_op, expressions, expressions, first)


def join_three_expressions(operator: Callable[[T, T, T], T],
                           expressions: List[T], bools: List[T], first: T) -> T:
    """
    Joins three expressions with ``operator`` in the same way as ``join_expressions``.
    """
    result = expressions[-1]
    for part_expr, part_bool in zip(reversed(expressions[:-1]),
                                    reversed(bools[:-1])):
        result = operator(part_expr, part_bool, result)
    return result


def construct_lambda_prefix(line: int, column: Optional[int]) -> str:
    """
    Creates an identifier for a lambda expression based on its line and column.
    """
    return 'lambda{0}_{1}'.format(line,
                                  'unknown' if column is None else column)


def pprint(node) -> str:
    """
    Pretty prints a Python AST node. When given a string, just returns it.
    """
    if not node:
        raise ValueError(node)
    if isinstance(node, str):
        return node
    if isinstance(node, ast.FunctionDef):
        # Mainly for debugging, whenever this happens it's almost certainly
        # wrong.
        raise ValueError(node)
    res = astunparse.unparse(node)
    res = res.replace('\n', '')
    return res


def get_target_name(node: ast.AST) -> str:
    """
    Returns the name of the function this node belongs to. If it's a call,
    that's the name of the call target, if it's a function, that function's
    name. For any other node, the name of the containing function,
    """
    if (not isinstance(node, ast.Call) and
            not isinstance(node, ast.FunctionDef)):
        node = get_containing_member(node)
    if isinstance(node, ast.FunctionDef):
        return node.name
    func = node.func
    if isinstance(func, ast.Name):
        func = func.id
    if isinstance(func, ast.Attribute):
        func = func.attr
    return func


def get_containing_member(node: ast.AST) -> Optional[ast.FunctionDef]:
    """
    Returns the function this node belongs to, if any.
    """
    member = node
    while not isinstance(member, ast.FunctionDef) and member is not None:
        if hasattr(member, '_parent'):
            member = member._parent
        else:
            member = None
    return member


def is_get_ghost_output(node: ast.Assign) -> bool:
    return (isinstance(node.value, ast.Call) and
            isinstance(node.value.func, ast.Name) and
            node.value.func.id == 'GetGhostOutput')


class OldExpressionCollector(ast.NodeVisitor):
    """A visitor that collects all expressions inside Old()-calls."""
    def __init__(self):
        self.expressions = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == 'Old':
            assert len(node.args) == 1
            self.expressions.append(node.args[0])
        else:
            self.generic_visit(node)


class OldExpressionTransformer(ast.NodeTransformer):
    """
    A visitor that replaces references to specific names by calls to arg(i), where
    i is the index of the name (given in self.arg_names).
    """
    def __init__(self):
        self.arg_names = []

    def visit_Name(self, node: ast.Name):
        if node.id in self.arg_names:
            index = self.arg_names.index(node.id)
            return ast.Call(func=ast.Name(id='arg', ctx=ast.Load()),
                            args=[ast.Num(n=index)],
                            keywords=[])
        return node


class SingletonFreshName:
    """
    This class wraps the fresh name facility in scope by using it only when
    a new name is given. It is designed to store and retrieve the fresh name
    based on the original name given.
    """

    def __init__(self, scope: 'PythonScope') -> None:
        self._fresh_name_dict = {}
        self._scope = scope

    def __call__(self, name: str) -> str:
        """
        Returns a fresh name for a given name and scope if enquired for the
        first time, otherwise returns the previously given fresh name.
        """
        if name not in self._fresh_name_dict:
            self._fresh_name_dict[name] = self._scope.get_fresh_name(name)
        return self._fresh_name_dict[name]


def string_to_int(string: str) -> int:
    """
    Computes an integer value that uniquely represents the given string.
    """
    result = 0
    for (index, char) in enumerate(string):
        result += pow(256, index) * ord(char)
    return result


def int_to_string(i: int) -> str:
    result = ''
    while i > 0:
        result += chr(i % 256)
        i = i // 256
    return result
