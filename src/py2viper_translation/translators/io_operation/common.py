"""Common code for both IO operation use and definition translation."""


import ast

from typing import List, Optional

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonIOExistentialVar,
    PythonVar,
)
from py2viper_translation.lib.typedefs import Expr
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.io_operation.utils import (
    construct_getter_name,
)


class IOOperationCommonTranslator(CommonTranslator):
    """Shared code between IO operation use and definition translation."""

    def translate_args(
            self, args: List[ast.expr],
            ctx: Context) -> List[Expr]:
        """Translate IO operation arguments to silver."""
        arg_exprs = []
        for arg in args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            assert not arg_stmt
            arg_exprs.append(arg_expr)
        return arg_exprs

    def create_result_getter(
            self, node: ast.Call, result: PythonVar, ctx: Context,
            sil_args: Optional[List[ast.Expr]] = None) -> Expr:
        """Construct a getter for an IO operation result."""
        position = self.no_position(ctx)
        info = self.no_info(ctx)

        operation = self.get_target(node, ctx)
        assert isinstance(operation, PythonIOOperation)

        if sil_args is None:
            py_args = node.args[:len(operation.get_parameters())]
            sil_args = self.translate_args(py_args, ctx)

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
        sil_args = self.translate_args(py_args, ctx)
        for parameter, py_arg, sil_arg in zip(parameters, py_args, sil_args):
            var_type = self.get_type(py_arg, ctx)
            var = PythonIOExistentialVar(parameter.name, py_arg, var_type)
            var.set_ref(sil_arg, None)
            ctx.set_alias(parameter.name, var)
            aliases.append(parameter.name)

        return aliases
