"""Translation of IO operation use."""


import ast

from typing import cast, List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonGlobalVar,
    PythonIOExistentialVar,
    PythonIOOperation,
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
from py2viper_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from py2viper_translation.translators.io_operation.utils import (
    get_parent,
    get_opened_operation,
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
        """Translate ``Open(io_operation)``.

        .. todo:: Vytautas

            Refactor this monster into method template.
        """
        assert ctx.actual_function
        io_ctx = ctx.io_open_context
        io_ctx.start_io_operation_open()

        operation = get_opened_operation(node, ctx)
        if operation.is_basic():
            raise_invalid_operation_use('open_basic_io_operation', node)

        statements = []

        operation_call = cast(ast.Call, node.args[0])
        py_args = operation_call.args
        if len(py_args) != len(operation.get_parameters()):
            raise_invalid_operation_use('result_used_argument', node)
        sil_args = self.translate_args(py_args, ctx)

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
        # TODO: Refactor: _set_up_aliases has exactly the same code.
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
            getter = self.create_result_getter(
                operation_call, result, ctx, sil_args=sil_args)
            # NOTE: sil_args must be translated in the context without
            # aliases.
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

    def _translate_results(
            self, operation: PythonIOOperation, node: ast.Call,
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
            raise_invalid_operation_use('result_mismatch', node)

        io_ctx = ctx.io_open_context
        equations = []
        for result, instance_expr in zip(results, result_instances):

            if not isinstance(instance_expr, ast.Name):
                raise_invalid_operation_use(
                    'not_variable_in_result_position', node)

            getter = self.create_result_getter(node, result, ctx)

            def add_comparison(var: PythonVarBase) -> Expr:
                """Create ``EqCmp`` between ``var`` and ``getter``."""
                comparison = self.viper.EqCmp(
                    getter, var.ref(), position, info)  # pylint: disable=cell-var-from-loop
                equations.append(comparison)

            def check(var: PythonVarBase) -> None:
                """Perform well-formedness checks."""
                if var.type != result.type:  # pylint: disable=cell-var-from-loop
                    raise_invalid_existential_var(
                        'defining_expression_type_mismatch', node)

            instance = cast(ast.Name, instance_expr)
            var_name = instance.id
            if var_name in ctx.var_aliases:
                var = ctx.var_aliases[var_name]
            else:
                var = ctx.actual_function.get_variable(var_name)
                assert var

            if io_ctx.contains_variable(var_name):
                # Variable denotes a result of the operation being opened.
                var = io_ctx.get_variable(var_name)
                assert isinstance(var, PythonVar)
                check(var)
                if io_ctx.is_variable_defined(var_name):
                    add_comparison(var)
                else:
                    io_ctx.define_variable(var_name, getter)
            elif isinstance(var, PythonIOExistentialVar):
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

    def _construct_full_perm(self, node: ast.Call,
                             ctx: Context) -> 'viper_ast.FullPerm':
        """Construct silver full perm AST node."""
        return self.viper.FullPerm(self.to_position(node, ctx),
                                   self.no_info(ctx))
