"""
This file contains code responsible for translating IO operations.
"""


import ast

from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonIOExistentialVar,
    PythonVar,
)
from py2viper_translation.lib.typedefs import StmtsAndExpr
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator
from typing import cast, List, Tuple

# Just to make mypy happy.
if False:         # pylint: disable=using-constant-test
    import viper  # pylint: disable=import-error,unused-import


def _construct_getter_name(operation: PythonIOOperation,
                           result: PythonVar) -> str:
    """ Utility function for constructing getter name.
    """
    return 'get__{0}__{1}'.format(
        operation.sil_name,
        result.sil_name,
    )


def _raise_invalid_operation_use(error_type: str, node: ast.AST) -> None:
    """ Raises InvalidProgramException.
    """
    raise InvalidProgramException(
        node,
        'invalid.io_operation_use.' + error_type,
    )


class IOOperationTranslator(CommonTranslator):
    """ Class responsible for translating IO operations.
    """

    def _construct_full_perm(self, node: ast.Call,
                             ctx: Context) -> 'viper.silver.ast.FullPerm':
        """
        Constructs silver full perm AST node.
        """
        return self.viper.FullPerm(self.to_position(node, ctx),
                                   self.no_info(ctx))

    def translate_io_operation(
            self, operation: PythonIOOperation,
            ctx: Context) -> Tuple[
                'viper.silver.ast.Predicate',
                List['viper.silver.ast.Function'],
                List['viper.silver.ast.Method']]:
        """ Translates IO operation to Silver.
        """
        args = [
            arg.decl
            for arg in operation.get_parameters()
        ]
        position = self.to_position(operation.node, ctx)
        info = self.no_info(ctx)

        predicate = self.viper.Predicate(operation.sil_name, args, None,
                                         position, info)

        getters = []
        for result in operation.get_results():
            name = _construct_getter_name(operation, result)
            typ = self.translate_type(result.type, ctx)
            getter = self.viper.Function(name, args, typ, [], [], None,
                                         position, info)
            getters.append(getter)

        return (
            predicate,
            getters,
            []
        )

    def translate_io_contractfunc_call(self, node: ast.Call,
                                       ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to a IO contract function such as ``token``.
        """
        func_name = get_func_name(node)
        if func_name == 'token':
            return self.translate_token(node, ctx)
        else:
            raise UnsupportedException(node)

    def translate_token(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translate a call to IO contract function ``token``.

        .. todo::

            Implement support for obligations. Currently, providing a
            measure for a token gives an assertion error.

        """
        assert len(node.args) == 1, "Obligations not implemented."
        place = node.args[0]
        place_stmt, place_expr = self.translate_expr(place, ctx)
        assert not place_stmt
        perm = self._construct_full_perm(node, ctx)
        return [], self.create_predicate_access('token', [place_expr], perm,
                                                node, ctx)

    def _translate_args(
            self, args: List[ast.expr],
            ctx: Context) -> List['viper.silver.ast.Expression']:
        """
        A helper method that translates IO operation arguments to
        silver.
        """
        arg_exprs = []
        for arg in args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            assert not arg_stmt
            arg_exprs.append(arg_expr)
        return arg_exprs

    def _translate_results(
            self, args: List[ast.Expr],
            operation: PythonIOOperation, node: ast.Call,
            ctx: Context) -> List['viper.silver.ast.Expression']:
        """
        A helper method that defines getters corresponding to operation
        results, or emits equalities between each result and getter
        definition.

        .. todo::

            Implement defining equalities between each result and getter
            definition.
        """

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        parameters_count = len(operation.get_parameters())
        result_instances = node.args[parameters_count:]
        results = operation.get_results()

        if len(result_instances) != len(results):
            _raise_invalid_operation_use('result_mismatch', node)

        for result, instance_expr in zip(results, result_instances):
            if not isinstance(instance_expr, ast.Name):
                _raise_invalid_operation_use(
                    'not_variable_in_result_position', node)
            instance = cast(ast.Name, instance_expr)
            var_name = instance.id
            if var_name not in ctx.actual_function.io_existential_vars:
                _raise_invalid_operation_use(
                    'variable_not_existential', node)
            var = ctx.actual_function.io_existential_vars[var_name]
            assert isinstance(var, PythonIOExistentialVar)
            if var.is_defined():
                # TODO: Implement: getter_result == getter_instance
                raise UnsupportedException(node)
            else:
                name = _construct_getter_name(operation, result)
                typ = self.translate_type(result.type, ctx)
                formal_args = [
                    arg.decl
                    for arg in operation.get_parameters()
                ]
                getter = self.viper.FuncApp(
                    name, args, position, info, typ, formal_args)
                var.ref = getter
        return []

    def translate_io_operation_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to an IO operation:

        1.  Emits a predicate corresponding to the operation.
        2.  Either defines getters corresponding to operation results,
            or emits equalities between each result and getter
            definition.
        """
        assert ctx.actual_function

        name = get_func_name(node)
        operation = ctx.program.io_operations[name]
        parameters_count = len(operation.get_parameters())
        args = self._translate_args(node.args[:parameters_count], ctx)
        perm = self._construct_full_perm(node, ctx)

        # Translate predicate.
        predicate = self.create_predicate_access(
            operation.sil_name, args, perm, node, ctx)

        # Translate results.
        self._translate_results(args, operation, node, ctx)
        # TODO: And expressions returned by _translate_results.
        return [], predicate
