"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""A helper class for translating IO operation Open."""


import ast

from typing import cast, List
from collections import OrderedDict

from nagini_translation.lib.context import Context
from nagini_translation.lib.io_context import IOOpenContext
from nagini_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonVar,
)
from nagini_translation.lib.resolver import get_target
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from nagini_translation.translators.io_operation.utils import (
    raise_invalid_operation_use,
)


def _get_opened_operation(
        node: ast.Call, ctx: Context) -> PythonIOOperation:
    """Get the operation that is being opened."""
    if (len(node.args) == 1 and
            isinstance(node.args[0], ast.Call) and
            isinstance(node.args[0].func, ast.Name)):
        containers = [ctx.module]
        containers.extend(ctx.module.get_included_modules())
        target = get_target(node.args[0], containers, None)
        if isinstance(target, PythonIOOperation):
            return target
    raise_invalid_operation_use('open_non_io_operation', node)


class Opener:
    """A class responsible for translating ``Open`` call."""

    def __init__(self, node: ast.Call, ctx: Context,
                 translator: IOOperationCommonTranslator,
                 full_perm: 'viper_ast.FullPerm') -> None:
        self._node = node
        self._ctx = ctx
        self._operation = _get_opened_operation(node, ctx)
        self._operation_call = cast(ast.Call, node.args[0])
        self._translator = translator
        self._full_perm = full_perm

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
        self._io_ctx.start_io_operation_open()

        statements = []

        self._check()
        sil_args = self._translate_arguments()
        statements.append(self._translate_exhale(sil_args))
        statements.extend(self._translate_inhale(sil_args))

        self._io_ctx.stop_io_operation_open()
        return (statements, None)

    def _check(self) -> None:
        """Check that operation open is well-formed."""
        if self._operation.is_basic():
            raise_invalid_operation_use('open_basic_io_operation',
                                        self._node)
        if (len(self._operation_call.args) !=
                len(self._operation.get_parameters())):
            raise_invalid_operation_use('result_used_argument', self._node)

    def _translate_arguments(self) -> List[Expr]:
        return self._translator.translate_args(
            self._operation_call.args, self._operation.get_parameters(),
            self._ctx)

    def _translate_exhale(self, sil_args: List[Expr]) -> Stmt:
        """Translate exhale of IO operation."""
        predicate = self._translator.create_predicate_access(
            self._operation.sil_name, sil_args, self._full_perm,
            self._node, self._ctx)
        exhale = self._viper.Exhale(predicate, self._position, self._info)
        return exhale

    def _translate_inhale(self, sil_args: List[Expr]) -> List[Stmt]:
        """Translate inhale of IO operation."""
        with self._ctx.aliases_context():
            self._define_input_aliases()
            self._define_output_aliases(sil_args)
            self._define_existential_variables()
            self._ctx.inlined_calls.append(self._operation)
            body = self._translate_body()
            alias_definitions = dict(self._io_ctx._open_var_alias_definitions)
            for alias in self._io_ctx._open_var_aliases:
                ref = self._io_ctx._open_var_aliases[alias].ref()
                replacement = alias_definitions[alias]
                body = body.replace(ref, replacement)
                for other_alias in self._io_ctx._open_var_alias_definitions:
                    if alias == other_alias:
                        continue
                    alias_definitions[other_alias] = alias_definitions[other_alias].replace(ref, replacement)
            self._ctx.inlined_calls.pop()
        return [self._emit_body_inhale(body)]

    def _define_existential_variables(self) -> None:
        """Define fresh local variables for stuff mentioned in IOExists.

        Make sure that they have fresh silver names. Add them to the
        context and variable aliases.
        """
        io_existential_vars = OrderedDict(
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

    def _define_output_aliases(self, sil_args: List[Expr]) -> None:
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
                sil_args=sil_args)
            self._io_ctx.define_variable(name, getter)

    def _translate_body(self) -> Expr:
        """Translate body.

        During translation defining getters are stored in the context
        and variables are replaced by variables created earlier. Note
        that existentials defined by ``existential == expression`` are
        not allowed because both use cases (fields and Result()) are
        forbidden inside IO operations.
        """
        statements, body_expression = self._translator.translate_expr(
            self._operation.get_body(), self._ctx,
            target_type=self._translator.viper.Bool, impure=True)
        assert not statements
        return body_expression

    def _emit_existential_variable_definitions(self) -> List[Stmt]:
        """Emit existential variable definitions.

        Emit equalities between created variables and their
        corresponding defining getters.
        """
        statements = []
        for var, definition in self._io_ctx.get_ordered_variable_defs():
            assignment = self._viper.LocalVarAssign(
                var.ref(), definition, self._position, self._info)
            statements.append(assignment)
        return statements

    def _emit_body_inhale(self, body: Expr) -> Stmt:
        """Emit inhale of the translate IO operation body."""
        inhale = self._viper.Inhale(
            body, self._position, self._info)
        return inhale

    def _add_local_var(self, name, var) -> None:
        sil_name = self._ctx.actual_function.get_fresh_name(name)
        var.process(sil_name, self._translator.translator)
        self._ctx.actual_function.locals[sil_name] = var
        self._io_ctx.add_variable(name, var)
        self._ctx.set_alias(name, var)
