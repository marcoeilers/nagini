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


def get_body_start_index(statements: List[ast.AST]) -> int:
    """
    Returns the index of the first statement that is not a method
    contract.

    .. note::

        In the case when a method has only a contract, the returned
        index is equal to ``len(statements)``.
    """
    body_index = 0
    try:
        while is_docstring(statements[body_index]):
            body_index += 1
        while is_io_existential(statements[body_index]):
            body_index += 1
        while is_pre(statements[body_index]):
            body_index += 1
        while is_post(statements[body_index]):
            body_index += 1
        while is_exception_decl(statements[body_index]):
            body_index += 1
    except IndexError:
        # This exception means that the method has only a contract.
        pass
    return body_index


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
    if not hasattr(node, '_parent') or not node._parent:
        return None
    return find_loop_for_previous(node._parent, name)


def join_expressions(operator: Callable[[T, T], T],
                     expressions: List[T]) -> T:
    """
    Joins expressions with ``operator``.

    This function joins expressions backwards (the last two expressions
    are most nested) in order to avoid Silicon issue
    `241 <https://bitbucket.org/viperproject/silicon/issues/241>`_.
    """
    result = expressions[-1]
    for part in reversed(expressions[:-1]):
        result = operator(part, result)
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
        # mainly for debugging, whenever this happens it's almost certainly
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
