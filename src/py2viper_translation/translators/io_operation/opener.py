"""A helper class for translating IO operation Open."""


import ast

from typing import cast

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.io_context import IOOpenContext
from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    StmtsAndExpr,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from py2viper_translation.translators.io_operation.utils import (
    raise_invalid_operation_use,
)


class Opener:
    """A class responsible for translating ``Open`` call."""

    def __init__(self, node: ast.Call, ctx: Context,
                 translator: IOOperationCommonTranslator,
                 full_perm: 'viper_ast.FullPerm') -> None:
        self._node = node
        self._ctx = ctx
        self._operation = self._get_opened_operation()
        self._operation_call = cast(ast.Call, node.args[0])
        self._translator = translator
        self._full_perm = full_perm

        # Translated stuff.
        self._sil_args = None
        self._body_expression = None
        self._statements = []

    @property
    def _io_ctx(self) -> IOOpenContext:
        return self._ctx.io_open_context

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper

    @property
    def _position(self) -> 'viper_ast.Position':
        return self._translator.to_position(self._node, self._ctx)

    @property
    def _info(self) -> 'viper_ast.Info':
        return self._translator.no_info(self._ctx)

    def translate(self) -> StmtsAndExpr:
        """Translate IO operation open."""
        assert not self._statements, "translate is called twice."
        self._io_ctx.start_io_operation_open()

        self._check()
        self._translate_arguments()
        self._translate_exhale()
        self._translate_inhale()

        self._io_ctx.stop_io_operation_open()
        return (self._statements, None)

    def _get_opened_operation(self) -> PythonIOOperation:
        """Get the operation that is being opened."""
        node = self._node
        ctx = self._ctx
        if (len(node.args) == 1 and
                isinstance(node.args[0], ast.Call) and
                isinstance(node.args[0].func, ast.Name)):
            name = node.args[0].func.id
            if name in ctx.program.io_operations:
                return ctx.program.io_operations[name]
        raise_invalid_operation_use('open_non_io_operation', node)

    def _check(self) -> None:
        """Check that operation open is well-formed."""
        if self._operation.is_basic():
            raise_invalid_operation_use('open_basic_io_operation',
                                        self._node)
        if (len(self._operation_call.args) !=
                len(self._operation.get_parameters())):
            raise_invalid_operation_use('result_used_argument', self._node)

    def _translate_arguments(self) -> None:
        self._sil_args = self._translator.translate_args(
            self._operation_call.args, self._ctx)

    def _translate_exhale(self) -> None:
        """Translate exhale of IO operation."""
        predicate = self._translator.create_predicate_access(
            self._operation.sil_name, self._sil_args, self._full_perm,
            self._node, self._ctx)
        exhale = self._viper.Exhale(predicate, self._position, self._info)
        self._statements.append(exhale)

    def _translate_inhale(self) -> None:
        """Translate inhale of IO operation."""
        with self._ctx.aliases_context():
            self._define_input_aliases()
            self._define_output_aliases()
            self._define_existential_variables()
            self._translate_body()
        self._emit_existential_variable_definitions()
        self._emit_body_inhale()

    def _define_existential_variables(self) -> None:
        """Define fresh local variables for stuff mentioned in IOExists.

        Make sure that they have fresh silver names. Add them to the
        context and variable aliases.
        """
        io_existential_vars = dict(
            (creator.name, creator.create_variable_instance())
            for creator in self._operation.get_io_existentials()
        )
        for name, var in io_existential_vars.items():
            self._add_local_var(name, var)

    def _define_input_aliases(self) -> None:
        """Set up aliases for input.

        Here we use existential variables during translation that are
        later replaced by silver expressions that were provided as
        arguments.
        """
        self._translator.set_up_io_operation_input_aliases(
            self._operation, self._operation_call, self._ctx)

    def _define_output_aliases(self) -> None:
        """Set up aliases for output.

        The same idea as with IOExists stuff, just we immediately
        provide their definitions because we know them.
        """
        for result in self._operation.get_results():
            name = result.name
            var = PythonVar(name, result.node, result.type)
            self._add_local_var(name, var)
            getter = self._translator.create_result_getter(
                self._operation_call, result, self._ctx,
                sil_args=self._sil_args)
            self._io_ctx.define_variable(name, getter)

    def _translate_body(self) -> None:
        """Translate body.

        During translation defining getters are stored in the context
        and variables are replaced by variables created earlier. Note
        that existentials defined by ``existential == expression`` are
        not allowed because both use cases (fields and Result()) are
        forbidden inside IO operations.
        """
        statements, self._body_expression = self._translator.translate_expr(
            self._operation.get_body(), self._ctx, expression=True)
        assert not statements

    def _emit_existential_variable_definitions(self) -> None:
        """Emit existential variable definitions.

        Emit equalities between created variables and their
        corresponding defining getters.
        """
        for var, definition in self._io_ctx.get_ordered_variable_defs():
            assignment = self._viper.LocalVarAssign(
                var.ref(), definition, self._position, self._info)
            self._statements.append(assignment)

    def _emit_body_inhale(self) -> None:
        """Emit inhale of the translate IO operation body."""
        inhale = self._viper.Inhale(
            self._body_expression, self._position, self._info)
        self._statements.append(inhale)

    def _add_local_var(self, name, var) -> None:
        sil_name = self._ctx.actual_function.get_fresh_name(name)
        var.process(sil_name, self._translator.translator)
        self._ctx.actual_function.locals[sil_name] = var
        self._io_ctx.add_variable(name, var)
        self._ctx.set_alias(name, var)
