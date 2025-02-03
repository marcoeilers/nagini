"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Common code for both IO operation use and definition translation."""


import ast

from typing import List, Optional

from nagini_translation.lib.constants import (
    BOXED_PRIMITIVES,
    PRIMITIVE_PREFIX,
)
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonIOExistentialVar,
    PythonVar,
)
from nagini_translation.lib.typedefs import Expr
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.translators.io_operation.utils import (
    construct_getter_name,
)


class IOOperationCommonTranslator(CommonTranslator):
    """Shared code between IO operation use and definition translation."""

    def translate_args(
            self, args: List[ast.expr],
            params,
            ctx: Context) -> List[Expr]:
        """Translate IO operation arguments to silver."""
        arg_exprs = []
        for arg, param in zip(args, params):
            typ = self.translate_type(param.type, ctx)
            arg_stmt, arg_expr = self.translate_expr(arg, ctx, target_type=typ)
            assert not arg_stmt
            arg_exprs.append(arg_expr)
        return arg_exprs

    def create_result_getter(
            self, node: ast.Call, result: PythonVar, ctx: Context,
            sil_args: List[ast.Expr] = None,
            operation: PythonIOOperation = None) -> Expr:
        """Construct a getter for an IO operation result."""
        position = self.no_position(ctx)
        info = self.no_info(ctx)

        if not operation:
            operation = self.get_target(node, ctx)
            assert isinstance(operation, PythonIOOperation)

        if sil_args is None:
            parameters = operation.get_parameters()
            py_args = node.args[:len(parameters)]
            sil_args = self.translate_args(py_args, parameters, ctx)

        getter_name = construct_getter_name(operation, result)
        typ = self.translate_type(result.type, ctx)
        formal_args = [
            arg.decl
            for arg in operation.get_parameters()
        ]

        getter = self.viper.FuncApp(
            getter_name, sil_args, position, info, typ, formal_args)
        return getter

    def set_up_io_operation_input_aliases(
            self, operation: PythonIOOperation, node: ast.Call,
            ctx: Context) -> List[str]:
        """Set up aliases from operation's parameters to its arguments."""
        aliases = []

        parameters = operation.get_parameters()
        py_args = node.args[:len(parameters)]
        sil_args = self.translate_args(py_args, parameters, ctx)
        for parameter, py_arg, sil_arg in zip(parameters, py_args, sil_args):
            var_type = self.get_type(py_arg, ctx).try_unbox()
            var = PythonIOExistentialVar(parameter.name, py_arg, var_type)
            var.set_ref(sil_arg, None)
            ctx.set_alias(parameter.name, var)
            aliases.append(parameter.name)

        return aliases
