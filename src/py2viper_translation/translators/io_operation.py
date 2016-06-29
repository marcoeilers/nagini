"""
This file contains code responsible for translating IO operations.

Translation of IO Existential Variables
=======================================

VeriFast has ``?a`` syntax which is essentially an assignment expression
that allows to link IO operations in contracts. However, neither Python,
nor Silver has assignment expressions.

``IOExists`` is a special construct that allows to define IO existential
variables (class ``PythonIOExistentialVar``) that can be used for
linking IO operations in contracts. For example::

    def read_int(t1: Place) -> Tuple[Place, int]:
        IOExists = lambda t2, value: (
            Requires(
                token(t1) and
                read_int_io(t1, value, t2)
            ),
            Ensures(
                token(t2) and
                t2 == Result()[0] and
                value == Result()[1]
            )
        )   # type: Callable[[Place, int], Tuple[bool, bool]]

Here ``t2`` and ``value`` are IO existential variables. Unlike normal
variables, existential variables are not created as variables on the
Silver level, but instead they are replaced with their definitions. A
definition of the existential variable is its first mention in a
contract, which must be one of:

1.  **IO operation's result.** In this case the definition of the
    existential variable is IO operation's getter. For example,
    ``read_int_io(t1, value, t2)`` in the example above defines
    ``value`` and ``t2``. As a result, in all subsequent uses
    ``value`` is translated to ``get__read_int_io__value(t1)`` and
    ``t2`` to ``get__read_int_io__t_post(t1)``.
2.  **Equality with already defined value.** The only accepted syntax in
    this case is ``existential_variable == something``. For example,
    ``2 == value`` would give an error because existential variable is
    on the right hand side. In this case, the definition of the
    existential variable is the right hand side of the equality.

    .. note::

        The defining equality must be a top level assertion because the
        following contract::

            (
                value == x.f
                if b
                else value == x.g
            ) and
            value == 2

        would be translated to:

        .. code-block:: silver

            (b ? True : x.f == x.g) && x.f == 2

        which is probably not what a programmer intended.
"""


import ast

from typing import Callable, cast, List, Tuple  # pylint: disable=unused-import

from py2viper_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonIOExistentialVar,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import Context
from py2viper_translation.translators.common import CommonTranslator

# Just to make mypy happy.
if False:         # pylint: disable=using-constant-test
    import viper  # pylint: disable=import-error,unused-import


def _construct_getter_name(operation: PythonIOOperation,
                           result: PythonVar) -> str:
    """Utility function for constructing getter name."""
    return 'get__{0}__{1}'.format(
        operation.sil_name,
        result.sil_name,
    )


def _raise_invalid_operation_use(error_type: str, node: ast.AST) -> None:
    """Raise InvalidProgramException."""
    raise InvalidProgramException(
        node,
        'invalid.io_operation_use.' + error_type,
    )


def _is_top_level_assertion(node: ast.expr) -> bool:
    """Check if assertion represented by node is top level."""
    def get_parent(node: ast.expr) -> ast.expr:
        """Just a helper function to make mypy happy."""
        return node._parent     # type: ignore
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


class IOOperationTranslator(CommonTranslator):
    """Class responsible for translating IO operations."""

    def _construct_full_perm(self, node: ast.Call,
                             ctx: Context) -> 'viper.silver.ast.FullPerm':
        """Construct silver full perm AST node."""
        return self.viper.FullPerm(self.to_position(node, ctx),
                                   self.no_info(ctx))

    def translate_io_operation(
            self, operation: PythonIOOperation,
            ctx: Context) -> Tuple[
                'viper.silver.ast.Predicate',
                List['viper.silver.ast.Function'],
                List['viper.silver.ast.Method']]:
        """Translate IO operation to Silver."""
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
        """Translate a call to a IO contract function.

        Currently supported functions:

        +   ``token``
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
        if len(node.args) != 1:
            raise UnsupportedException(
                node, "Obligations not implemented.")
        place = node.args[0]
        place_stmt, place_expr = self.translate_expr(place, ctx)
        assert not place_stmt
        perm = self._construct_full_perm(node, ctx)
        return [], self.create_predicate_access('token', [place_expr], perm,
                                                node, ctx)

    def _translate_args(
            self, args: List[ast.expr],
            ctx: Context) -> List[Expr]:
        """Translate IO operation arguments to silver."""
        arg_exprs = []
        for arg in args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            assert not arg_stmt
            arg_exprs.append(arg_expr)
        return arg_exprs

    def _translate_results(
            self, args: List[ast.Expr],
            operation: PythonIOOperation, node: ast.Call,
            ctx: Context) -> List[Expr]:
        """Translate IO operation results.

        That is: define getters corresponding to operation results or
        emit equalities between each result and getter definition.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        parameters_count = len(operation.get_parameters())
        result_instances = node.args[parameters_count:]
        results = operation.get_results()

        if len(result_instances) != len(results):
            _raise_invalid_operation_use('result_mismatch', node)

        equations = []
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

            name = _construct_getter_name(operation, result)
            typ = self.translate_type(result.type, ctx)
            formal_args = [
                arg.decl
                for arg in operation.get_parameters()
            ]
            getter = self.viper.FuncApp(
                name, args, position, info, typ, formal_args)

            if var.is_defined():
                comparison = self.viper.EqCmp(getter, var.ref,
                                              position, info)
                equations.append(comparison)
            else:
                var.ref = getter
        return equations

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
        args = self._translate_args(node.args[:parameters_count], ctx)
        perm = self._construct_full_perm(node, ctx)

        # Translate predicate.
        predicate = self.create_predicate_access(
            operation.sil_name, args, perm, node, ctx)

        # Translate results.
        equations = self._translate_results(args, operation, node, ctx)

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
        if (_is_top_level_assertion(node) and
                isinstance(node, ast.Compare)):
            if (len(node.ops) == 1 and
                    len(node.comparators) == 1 and
                    isinstance(node.left, ast.Name) and
                    isinstance(node.ops[0], ast.Eq)):
                var = ctx.actual_function.get_variable(node.left.id)
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
        var = ctx.actual_function.get_variable(name_node.id)
        var.ref = right
