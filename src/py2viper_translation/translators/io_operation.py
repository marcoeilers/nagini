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

------------
Known Issues
------------

Heap Dependent Getters
----------------------

If one of the IO operation arguments is a field, then the emitted
getters are heap dependent. For example, the value of place ``t2``
depends on field ``self.int_field``::

    write_int_io(t1, self.int_field, t2)

This has interesting consequences such as:

1.  Postcondition must have access to ``self.int_field``, otherwise
    ``t2`` getter is not framed::

        IOExists1(Place)(
            lambda t2: (
            Requires(
                Acc(self.int_field) and
                write_int_io(t1, self.int_field, t2)
            ),
            Ensures(
                t2 == Result() # ERROR: not.wellformed:insufficient.permission
            ),
            )
        )

2.  Similarly, if defining getter is heap dependent and guarded by
    conditional, other branch fails well-formedness check::

        Requires(
            token(t1) and
            (
                Acc(self.int_field1, 1/2) and
                write_int_io(t1, self.int_field1, t2)
            ) if b else (
                Acc(self.int_field2, 1/2) and
                write_int_io(t1, self.int_field2, t2)
                               # ERROR: not.wellformed:insufficient.permission
            )
        ),

3.  If defining getter is changed from heap independent in overridden
    method to heap dependent in a overriding method and overriding
    method takes all permission to the heap location, the behavioural
    subtyping check fails because information about getter equality is
    havocked.

Currently, the plan is to ignore the problem because storing arguments
in fields should not be too common in practise:

1.  The Petri Net provided at the entry point cannot depend on the heap
    – otherwise also permissions has to be provided at the entry
    point, which does not make much sense.
2.  It is not allowed to have permissions in non-basic IO operation
    definitions.

    .. todo:: Vytautas

        Implement this check.

.. todo:: Vytautas

    Things to investigate:

    1.  Does wrapping getters in ``old`` in postcondition solve the
        issue of having to provide permissions to fields in
        postcondition?
"""


import ast

from typing import Callable, cast, List, Tuple  # pylint: disable=unused-import

from py2viper_contracts.contracts import CONTRACT_WRAPPER_FUNCS
from py2viper_translation.lib.program_nodes import (
    PythonGlobalVar,
    PythonIOOperation,
    PythonIOExistentialVar,
    PythonVar,
    PythonVarBase,
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


def _raise_invalid_existential_var(error_type: str, node: ast.AST) -> None:
    """Raise InvalidProgramException."""
    raise InvalidProgramException(
        node,
        'invalid.io_existential_var.' + error_type,
    )


def _raise_invalid_get_ghost_output(error_type: str, node: ast.AST) -> None:
    """Raise InvalidProgramException."""
    raise InvalidProgramException(
        node,
        'invalid.get_ghost_output.' + error_type,
    )


def _is_top_level_assertion(node: ast.expr) -> bool:
    """Check if assertion represented by node is top level."""
    def get_parent(node: ast.expr) -> ast.expr:
        """A helper function to get a parent node."""
        # _parent is not a node field, it is added dynamically by our
        # code. That is why mypy reports an error here.
        if hasattr(node, '_parent'):
            return node._parent     # type: ignore
        else:
            return None
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


def _get_openned_operation(
        node: ast.Call, ctx: Context) -> PythonIOOperation:
    """Get the operation that is being opened."""
    if (len(node.args) == 1 and
            isinstance(node.args[0], ast.Call) and
            isinstance(node.args[0].func, ast.Name)):
        name = node.args[0].func.id
        if name in ctx.program.io_operations:
            return ctx.program.io_operations[name]
    _raise_invalid_operation_use('open_non_io_operation', node)


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
            return self._translate_token(node, ctx)
        elif func_name == 'Open':
            return self._translate_open(node, ctx)
        else:
            raise UnsupportedException(node,
                                       'Unsupported contract function.')

    def _translate_token(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translate a call to IO contract function ``token``.

        .. todo:: Vytautas

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

    def _translate_open(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate ``Open(io_operation)``.

        .. todo:: Vytautas

            Refactor this monster into method template.
        """
        assert ctx.actual_function
        io_ctx = ctx.io_open_context
        io_ctx.start_io_operation_open()

        operation = _get_openned_operation(node, ctx)
        if operation.is_basic():
            _raise_invalid_operation_use('open_basic_io_operation', node)

        statements = []

        py_args = cast(ast.Call, node.args[0]).args
        if len(py_args) != len(operation.get_parameters()):
            _raise_invalid_operation_use('result_used_argument', node)
        sil_args = self._translate_args(py_args, ctx)

        perm = self._construct_full_perm(node, ctx)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        # Exhale.
        predicate = self.create_predicate_access(
            operation.sil_name, sil_args, perm, node, ctx)
        statements.append(self.viper.Exhale(predicate, position, info))

        # Inhale.

        body = operation.get_body()

        open_aliases = []

        # Define fresh local variables for stuff mentioned in IOExists.
        # Make sure that they have fresh silver names. Add them to the
        # context and variable aliases.
        io_existential_vars = dict(
            (creator.name, creator.create_variable_instance())
            for creator in operation.get_io_existentials()
        )

        for name, var in io_existential_vars.items():
            sil_name = ctx.actual_function.get_fresh_name(name)
            var.process(sil_name, self.translator)
            ctx.actual_function.locals[sil_name] = var
            io_ctx.add_variable(name, var)
            ctx.set_alias(name, var)
            open_aliases.append(name)

        # Set up aliases for input. Here we use existential variables
        # during translation that are later replaced by silver
        # expressions that were provided as arguments.
        for parameter, py_arg, sil_arg in zip(
                operation.get_parameters(), py_args, sil_args):
            var_type = self.get_type(py_arg, ctx)
            var = PythonIOExistentialVar(parameter.name, py_arg, var_type)
            var.set_ref(sil_arg)
            ctx.set_alias(parameter.name, var)
            open_aliases.append(parameter.name)

        # Set up aliases for output. The same idea as with IOExists
        # stuff, just we immediately provide their definitions because
        # we know them.
        for result in operation.get_results():
            name = result.name
            var = PythonVar(name, result.node, result.type)
            sil_name = ctx.actual_function.get_fresh_name(name)
            var.process(sil_name, self.translator)
            ctx.actual_function.locals[sil_name] = var
            io_ctx.add_variable(name, var)
            getter = self._create_result_getter(
                sil_args, operation, result, ctx, position, info)
            io_ctx.define_variable(name, getter)
            ctx.set_alias(name, var)
            open_aliases.append(name)

        # Translate body. During translation defining getters are stored
        # in the context and variables are replaced by variables created
        # earlier. Note that existentials defined by
        # ``existential == expression`` are not allowed because both use
        # cases (fields and Result()) are forbidden inside IO
        # operations.
        body_statements, body_expression = self.translate_expr(
            body, ctx, expression=True)
        assert not body_statements

        # Remove all created aliases.
        for alias in open_aliases:
            ctx.remove_alias(alias)

        # Emit equalities among created variables and their
        # corresponding defining getters.
        for var, definition in io_ctx.get_ordered_variable_defs():
            assignment = self.viper.LocalVarAssign(var.ref(), definition,
                                                   position, info)
            statements.append(assignment)

        # Emit inhale of the translated body.
        statements.append(self.viper.Inhale(body_expression, position, info))

        io_ctx.stop_io_operation_open()

        return (statements, None)

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

    def _create_result_getter(
            self, args: List[ast.Expr], operation, result, ctx,
            position, info):
        """Construct a getter for an IO operation result."""
        name = _construct_getter_name(operation, result)
        typ = self.translate_type(result.type, ctx)
        formal_args = [
            arg.decl
            for arg in operation.get_parameters()
        ]
        getter = self.viper.FuncApp(
            name, args, position, info, typ, formal_args)
        return getter

    def _translate_results(
            self, args: List[ast.Expr],
            operation: PythonIOOperation, node: ast.Call,
            ctx: Context) -> List[Expr]:
        """Translate IO operation results.

        That is: define getters corresponding to operation results or
        emit equalities between each result and getter definition.

        .. todo:: Vytautas

            Refactor this monster.

        .. todo:: Vytautas

            Allow arbitrary expressions in result positions, not only
            variables.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        parameters_count = len(operation.get_parameters())
        result_instances = node.args[parameters_count:]
        results = operation.get_results()

        if len(result_instances) != len(results):
            _raise_invalid_operation_use('result_mismatch', node)

        io_ctx = ctx.io_open_context
        equations = []
        for result, instance_expr in zip(results, result_instances):

            if not isinstance(instance_expr, ast.Name):
                _raise_invalid_operation_use(
                    'not_variable_in_result_position', node)

            getter = self._create_result_getter(
                args, operation, result, ctx, position, info)

            def add_comparison(var: PythonVarBase) -> Expr:
                """Create ``EqCmp`` between ``var`` and ``getter``."""
                comparison = self.viper.EqCmp(
                    getter, var.ref(), position, info)  # pylint: disable=cell-var-from-loop
                equations.append(comparison)

            def check(var: PythonVarBase) -> None:
                """Perform well-formedness checks."""
                if var.type != result.type:  # pylint: disable=cell-var-from-loop
                    _raise_invalid_existential_var(
                        'defining_expression_type_mismatch', node)

            instance = cast(ast.Name, instance_expr)
            var_name = instance.id

            if io_ctx.contains_variable(var_name):
                # Variable denotes a result of the operation being opened.
                var = io_ctx.get_variable(var_name)
                assert isinstance(var, PythonVar)
                check(var)
                if io_ctx.is_variable_defined(var_name):
                    add_comparison(var)
                else:
                    io_ctx.define_variable(var_name, getter)
            elif var_name in ctx.actual_function.io_existential_vars:
                var = ctx.actual_function.io_existential_vars[var_name]
                assert isinstance(var, PythonIOExistentialVar)
                check(var)
                if var.is_defined():
                    add_comparison(var)
                else:
                    var.set_ref(getter)
            else:
                # Normal variable, which is already defined.
                var = ctx.actual_function.get_variable(var_name)
                assert var and isinstance(var, (PythonVar, PythonGlobalVar))
                check(var)
                add_comparison(var)

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

        expression_type = self.get_type(node.comparators[0], ctx)
        if var.type != expression_type:
            _raise_invalid_existential_var(
                'defining_expression_type_mismatch', node)

        var.set_ref(right)

    def translate_get_ghost_output(
            self, node: ast.Assign, ctx: Context) -> List[Stmt]:
        """Translate ``GetGhostOutput``."""
        if len(node.targets) != 1:
            _raise_invalid_get_ghost_output('multiple_targets', node)
        if not isinstance(node.targets[0], ast.Name):
            _raise_invalid_get_ghost_output('target_not_variable', node)
        target_name = cast(ast.Name, node.targets[0]).id
        target = ctx.actual_function.get_variable(target_name)
        assert target

        operation_call, result_name_node = cast(ast.Call, node.value).args

        if not isinstance(result_name_node, ast.Str):
            _raise_invalid_get_ghost_output('result_identifier_not_str', node)
        result_name = cast(ast.Str, result_name_node).s

        if not (isinstance(operation_call, ast.Call) and
                isinstance(operation_call.func, ast.Name)):
            _raise_invalid_get_ghost_output('argument_not_io_operation', node)
        operation_call = cast(ast.Call, operation_call)
        operation_name = cast(ast.Name, operation_call.func).id

        if operation_name not in ctx.program.io_operations:
            _raise_invalid_get_ghost_output('argument_not_io_operation', node)
        operation = ctx.program.io_operations[operation_name]

        result = None
        for result in operation.get_results():
            if result.name == result_name:
                break
        else:
            _raise_invalid_get_ghost_output('invalid_result_identifier', node)
        assert result

        if result.type != target.type:
            _raise_invalid_get_ghost_output('type_mismatch', node)

        # TODO: (Vytautas) Refactor this code duplication.
        py_args = operation_call.args
        if len(py_args) != len(operation.get_parameters()):
            _raise_invalid_operation_use('result_used_argument', node)
        sil_args = self._translate_args(py_args, ctx)

        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        getter = self._create_result_getter(
            sil_args, operation, result, ctx, position, info)

        assignment = self.viper.LocalVarAssign(target.ref(), getter,
                                               position, info)

        return [assignment]
