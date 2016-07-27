"""Translation of IO operation use."""


import ast

from typing import cast, List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonIOExistentialVar,
    PythonIOOperation,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from py2viper_translation.translators.io_operation.opener import Opener
from py2viper_translation.translators.io_operation.result_translator import (
    ResultTranslator,
)
from py2viper_translation.translators.io_operation.utils import (
    get_parent,
    get_variable,
    is_top_level_assertion,
    raise_invalid_operation_use,
    raise_invalid_existential_var,
    raise_invalid_get_ghost_output,
)


class IOOperationUseTranslator(IOOperationCommonTranslator):
    """Class responsible for translating IO operation use."""

    def translate_io_operation_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        """Translate a call to an IO operation.

        That is:

        1.  Emit a predicate access corresponding to the operation.
        2.  Either define getter invocations corresponding to the
            operation results, or emit equalities between each result
            and already defined getter invocation.
        """
        assert ctx.actual_function

        name = get_func_name(node)
        operation = ctx.program.io_operations[name]
        parameters_count = len(operation.get_parameters())
        args = self.translate_args(node.args[:parameters_count], ctx)
        perm = self._construct_full_perm(node, ctx)

        # Translate predicate.
        predicate = self.create_predicate_access(
            operation.sil_name, args, perm, node, ctx)

        # Translate results.
        equations = self._translate_results(operation, node, ctx)

        # And everything.
        expr = predicate
        for equation in equations:
            expr = self.viper.And(expr, equation,
                                  self.to_position(node, ctx),
                                  self.no_info(ctx))
        return [], expr

    def is_io_existential_defining_equality(self, node: ast.expr,
                                            ctx: Context) -> bool:
        """Check if ``node`` defines IO existential variable.

        That is, node is equality of form:
        ``existential_variable == something``.
        """
        if (is_top_level_assertion(node) and
                isinstance(node, ast.Compare)):
            if (len(node.ops) == 1 and
                    len(node.comparators) == 1 and
                    isinstance(node.left, ast.Name) and
                    isinstance(node.ops[0], ast.Eq)):
                var = get_variable(node.left.id, ctx)
                return (
                    isinstance(var, PythonIOExistentialVar) and
                    not var.is_defined())
        return False

    def define_io_existential(self, node: ast.Compare, ctx: Context) -> None:
        """From defining equality defines IO existential variable."""
        assert self.is_io_existential_defining_equality(node, ctx)

        # TODO: The result of this call must not only be an expression,
        # but a pure expression.
        right_stmt, right = self.translate_expr(
            node.comparators[0], ctx,
            expression=True)
        assert not right_stmt   # Should be handled by expression=True.

        name_node = cast(ast.Name, node.left)
        var = get_variable(name_node.id, ctx)

        expression_type = self.get_type(node.comparators[0], ctx)
        if var.type != expression_type:
            raise_invalid_existential_var(
                'defining_expression_type_mismatch', node)

        var.set_ref(right)

    def translate_get_ghost_output(
            self, node: ast.Assign, ctx: Context) -> List[Stmt]:
        """Translate ``GetGhostOutput``."""
        if len(node.targets) != 1:
            raise_invalid_get_ghost_output('multiple_targets', node)
        if not isinstance(node.targets[0], ast.Name):
            raise_invalid_get_ghost_output('target_not_variable', node)
        target_name = cast(ast.Name, node.targets[0]).id
        target = ctx.actual_function.get_variable(target_name)
        assert target

        operation_call, result_name_node = cast(ast.Call, node.value).args

        if not isinstance(result_name_node, ast.Str):
            raise_invalid_get_ghost_output('result_identifier_not_str', node)
        result_name = cast(ast.Str, result_name_node).s

        if not (isinstance(operation_call, ast.Call) and
                isinstance(operation_call.func, ast.Name)):
            raise_invalid_get_ghost_output('argument_not_io_operation', node)
        operation_call = cast(ast.Call, operation_call)
        operation_name = cast(ast.Name, operation_call.func).id

        if operation_name not in ctx.program.io_operations:
            raise_invalid_get_ghost_output('argument_not_io_operation', node)
        operation = ctx.program.io_operations[operation_name]

        result = None
        for result in operation.get_results():
            if result.name == result_name:
                break
        else:
            raise_invalid_get_ghost_output('invalid_result_identifier', node)
        assert result

        if result.type != target.type:
            raise_invalid_get_ghost_output('type_mismatch', node)

        if len(operation_call.args) != len(operation.get_parameters()):
            raise_invalid_operation_use('result_used_argument', node)
        getter = self.create_result_getter(operation_call, result, ctx)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        assignment = self.viper.LocalVarAssign(target.ref(), getter,
                                               position, info)

        return [assignment]

    def translate_io_contractfunc_call(self, node: ast.Call,
                                       ctx: Context) -> StmtsAndExpr:
        """Translate a call to a IO contract function.

        Currently supported functions:

        +   ``token``
        +   ``ctoken``
        +   ``Open``
        """
        func_name = get_func_name(node)
        if func_name == 'token':
            return self._translate_token(node, ctx)
        elif func_name == 'ctoken':
            return self._translate_ctoken(node, ctx)
        elif func_name == 'Open':
            return self._translate_open(node, ctx)
        else:
            raise UnsupportedException(node,
                                       'Unsupported contract function.')

    def _translate_token(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to IO contract function ``token``.

        .. todo:: Vytautas

            Implement support for obligations. Currently, providing a
            measure for a token gives an assertion error.
        """
        if len(node.args) != 1:
            raise UnsupportedException(
                node, "Obligations not implemented.")
        place = node.args[0]
        place_stmt, place_expr = self.translate_expr(place, ctx,
                                                     expression=True)
        assert not place_stmt
        perm = self._construct_full_perm(node, ctx)
        return [], self.create_predicate_access('token', [place_expr], perm,
                                                node, ctx)

    def _translate_ctoken(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to IO contract function ``ctoken``."""
        assert len(node.args) == 1
        if ctx.actual_function.name != 'Gap':
            parent = get_parent(node)
            while parent is not None:
                if (isinstance(parent, ast.Call) and
                        isinstance(parent.func, ast.Name) and
                        parent.func.id == 'Ensures'):
                    # ctoken in postcondition is unsound.
                    raise InvalidProgramException(
                        node,
                        'invalid.postcondition.ctoken_not_allowed',
                    )
                parent = get_parent(parent)
        place = node.args[0]
        place_stmt, place_expr = self.translate_expr(
            place, ctx, expression=True)
        assert not place_stmt
        perm = self._construct_full_perm(node, ctx)
        return [], self.create_predicate_access('ctoken', [place_expr], perm,
                                                node, ctx)

    def _translate_open(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``Open(io_operation)``."""
        assert ctx.actual_function
        full_perm = self._construct_full_perm(node, ctx)
        opener = Opener(node, ctx, self, full_perm)
        return opener.translate()

    def _translate_results(
            self, operation: PythonIOOperation, node: ast.Call,
            ctx: Context) -> List[Expr]:
        """Translate IO operation results.

        That is: define getters corresponding to operation results or
        emit equalities between each result and getter definition.
        """
        result_translator = ResultTranslator(operation, node, self, ctx)
        return result_translator.translate()

    def _construct_full_perm(self, node: ast.Call,
                             ctx: Context) -> 'viper_ast.FullPerm':
        """Construct silver full perm AST node."""
        return self.viper.FullPerm(self.to_position(node, ctx),
                                   self.no_info(ctx))
