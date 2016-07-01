import ast
import astunparse

from typing import Optional


cache = {}


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


errors = {
    'assignment.failed': lambda n: 'Assignment might fail.',
    'call.failed': lambda n: 'Method call might fail.',
    'not.wellformed': lambda n: 'Contract might not be well-formed.',
    'call.precondition':
        lambda n: 'The precondition of method ' + get_target_name(n) +
                  ' might not hold.',
    'application.precondition':
        lambda n: 'Precondition of function ' + get_target_name(n) +
                  ' might not hold.',
    'exhale.failed': lambda n: 'Exhale might fail.',
    'inhale.failed': lambda n: 'Inhale might fail.',
    'if.failed': lambda n: 'Conditional statement might fail.',
    'while.failed': lambda n: 'While statement might fail.',
    'assert.failed': lambda n: 'Assert might fail.',
    'postcondition.violated':
        lambda n: 'Postcondition of ' + get_containing_member(n).name +
                  ' might not hold.',
    'fold.failed': lambda n: 'Fold might fail.',
    'unfold.failed': lambda n: 'Unfold might fail.',
    'invariant.not.preserved':
        lambda n: 'Loop invariant might not be preserved.',
    'invariant.not.established':
        lambda n: 'Loop invariant might not hold on entry.',
    'function.not.wellformed':
        lambda n: 'Function ' + get_containing_member(n).name +
                  ' might not be well-formed.',
    'predicate.not.wellformed':
        lambda n: 'Predicate ' + get_containing_member(n).name +
                  ' might not be well-formed.',
}

reasons = {
    'assertion.false': lambda n: 'Assertion ' + pprint(n) + ' might not hold.',
    'receiver.null': lambda n: 'Receiver of ' + pprint(n) + ' might be null.',
    'division.by.zero': lambda n: 'Divisor ' + pprint(n) + ' might be zero.',
    'negative.permission':
        lambda n: 'Fraction ' + pprint(n) + ' might be negative.',
    'insufficient.permission':
        lambda n: 'There might be insufficient permission to access ' +
                  pprint(n) + '.',
}


def error_msg(error: 'silver.verifier.AbstractError') -> str:
    """
    Creates an appropriate error message (referring to the responsible Python
    code) for the given Viper error.
    """
    pos_string = str(error.pos())
    got_proper_position = False
    error_id = error.fullId().split(':')
    reason_ = error.reason()
    reason_offending = error.reason().offendingNode()
    reason_pos = error.reason().offendingNode().pos()
    reason_string = None
    if hasattr(reason_pos, 'id'):
        reason_pos = reason_pos.id()
        reason_entry = cache[reason_pos]
        reason_node = reason_entry[0]
        reason_string = reason_entry[2]
        if reason_entry[1]:
            got_proper_position = True
        for via in reason_entry[1]:
            pos_string += ', via ' + via[0] + ' at ' + str(via[1])
    else:
        reason_file = reason_pos.file()
        reason_node = None
    reason = reason_string if reason_string else reason_node
    if not reason:
        reason = str(reason_offending)
    reason_msg = reasons[error_id[1]](reason)
    error_pos = error.pos()
    if hasattr(error_pos, 'id'):
        error_pos = error_pos.id()
        error_entry = cache[error_pos]
        error_node = error_entry[0]
        if not got_proper_position:
            for via in error_entry[1]:
                pos_string += ', via ' + via[0] + ' at ' + str(via[1])
    else:
        off = error.offendingNode()
        off_pos = off.pos()
        error_node = None
    error_msg = errors[error_id[0]](error_node)
    return error_msg + ' ' + reason_msg + ' (' + pos_string + ')'
