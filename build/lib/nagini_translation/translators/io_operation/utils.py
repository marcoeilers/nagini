"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Utility functions."""


import ast

from nagini_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonVarBase,
)
from nagini_translation.lib.util import (
    InvalidProgramException,
)


def construct_getter_name(operation: PythonIOOperation,
                          result: PythonVarBase) -> str:
    """Utility function for constructing getter name."""
    return 'get__{0}__{1}'.format(
        operation.sil_name,
        result.sil_name,
    )


def raise_invalid_operation_use(error_type: str, node: ast.AST) -> None:
    """Raise InvalidProgramException."""
    raise InvalidProgramException(
        node,
        'invalid.io_operation_use.' + error_type,
    )


def raise_invalid_existential_var(error_type: str, node: ast.AST) -> None:
    """Raise InvalidProgramException."""
    raise InvalidProgramException(
        node,
        'invalid.io_existential_var.' + error_type,
    )


def raise_invalid_get_ghost_output(error_type: str, node: ast.AST) -> None:
    """Raise InvalidProgramException."""
    raise InvalidProgramException(
        node,
        'invalid.get_ghost_output.' + error_type,
    )


def get_parent(node: ast.expr) -> ast.expr:
    """A helper function to get a parent node."""
    # _parent is not a node field, it is added dynamically by our
    # code. That is why mypy reports an error here.
    if hasattr(node, '_parent'):
        return node._parent     # pylint: disable=protected-access
    else:
        return None


def is_top_level_assertion(node: ast.expr) -> bool:
    """Check if assertion represented by node is top level."""
    parent = get_parent(node)
    while (isinstance(parent, ast.BoolOp) and
           isinstance(parent.op, ast.And)):
        node = parent
        parent = get_parent(node)
    if (isinstance(parent, ast.Call) and
            isinstance(parent.func, ast.Name)):
        func_name = parent.func.id
        return func_name in CONTRACT_WRAPPER_FUNCS
    return False


def get_variable(var_name: str, ctx: Context) -> PythonVarBase:
    """Return variable by taking into account aliasing."""
    if var_name in ctx.var_aliases:
        var = ctx.var_aliases[var_name]
    else:
        var = ctx.actual_function.get_variable(var_name)
        assert var
    return var
