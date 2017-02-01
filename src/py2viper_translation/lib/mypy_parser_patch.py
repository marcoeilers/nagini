"""
Monkey-patches the mypy parser to add column information to the mypy AST.
More precisely, we monkey-patch the transformer that takes the normal
Python AST and turns it into a mypy AST to add, for every node, the column
information (if any) from the original node to the 'column' field of the new
node.

We need the column information because otherwise we have no way to know
the precise types of different references to the same variable in the same line
if they are different (which they may be because of isinstance checks).
"""

import mypy.fastparse

from functools import wraps


def with_column(f):
    """
    Decorator for functions belonging to the translation from Python AST to
    mypy AST. Adds the column information from the Python node to the column
    field of the mypy node.
    """
    @wraps(f)
    def wrapper(self, ast):
        node = f(self, ast)
        if hasattr(ast, 'col_offset'):
            node.column = ast.col_offset
        return node
    return wrapper


# Monkey-patch mypy's AST converter to add column information
ASTConverter = mypy.fastparse.ASTConverter
for name in dir(ASTConverter):
    m = getattr(ASTConverter, name)
    if callable(m) and name.startswith('visit_'):
        setattr(ASTConverter, name, with_column(m))

recorded_type_args = {}
last_call = [None]

def record_current_call(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        context = args[5]
        if hasattr(context, 'line') and hasattr(context, 'column') and context.line >= 0:
            last_call[0] = str(context.line) + '___' + str(context.column)
        return res
    return wrapper


def record_args(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        recorded_type_args[last_call[0]] = res
        return res
    return wrapper

ExpressionChecker = mypy.checkexpr.ExpressionChecker
f = ExpressionChecker.infer_function_type_arguments
setattr(ExpressionChecker, 'infer_function_type_arguments', record_current_call(f))

checkexpr = mypy.checkexpr
f = checkexpr.infer_function_type_arguments
setattr(checkexpr, 'infer_function_type_arguments', record_args(f))
