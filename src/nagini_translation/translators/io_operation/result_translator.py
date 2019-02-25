"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""A helper class for translating IO operation results."""


import ast
import copy

from typing import cast, List

from nagini_translation.lib.constants import EVAL_IO_SIGNATURE
from nagini_translation.lib.context import Context
from nagini_translation.lib.io_context import IOOpenContext
from nagini_translation.lib.program_nodes import (
    PythonIOOperation,
    PythonIOExistentialVar,
    PythonGlobalVar,
    PythonVar,
    PythonVarBase,
)
from nagini_translation.lib.typedefs import (
    Expr,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)
from nagini_translation.translators.io_operation.utils import (
    raise_invalid_operation_use,
    raise_invalid_existential_var,
)


class IOOperationResult:
    """Translation state of a specific IO operation result."""

    def __init__(self, node: ast.Call, definition: PythonVar,
                 instance: ast.expr) -> None:
        self._node = node

        self.definition = definition
        """Result as defined in IO operation definition."""

        self.instance = instance
        """Result as given in IO operation call."""

        self.getter = None
        """Getter associated with this result."""

        self.var_name = None
        """Variable name mentioned in IO operation call."""

        self._var = None

    @property
    def node(self) -> ast.Call:
        """Get the AST node for position."""
        return self._node

    @property
    def var(self) -> PythonVarBase:
        """The resolved variable that was referred by ``var_name``."""
        assert self._var is not None
        return self._var

    @var.setter
    def var(self, var: PythonVarBase) -> None:
        assert var is not None
        if var.type != self.definition.type:
            if not (self.var_name == EVAL_IO_SIGNATURE[3] and
                    self._node.func.id == EVAL_IO_SIGNATURE[0]):
                raise_invalid_existential_var(
                    'defining_expression_type_mismatch', self._node)
        self._var = var


class ResultTranslator:
    """Translate variables bound by IO operation call.

    .. todo:: Vytautas

        Check if it makes sense to have arbitrary expressions in result
        positions. (Currently, only variables are allowed.)
    """

    def __init__(
            self, operation: PythonIOOperation, node: ast.Call,
            translator: IOOperationCommonTranslator, ctx: Context) -> None:
        self._operation = operation
        self._node = node
        self._ctx = ctx
        self._translator = translator

        # Translated stuff.
        self._equations = []

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper

    @property
    def _position(self) -> 'viper_ast.Position':
        return self._translator.to_position(self._node, self._ctx)

    @property
    def _info(self) -> 'viper_ast.Info':
        return self._translator.no_info(self._ctx)

    @property
    def _io_ctx(self) -> IOOpenContext:
        return self._ctx.io_open_context

    @property
    def _result_definitions(self) -> List[PythonVar]:
        """Return results as defined in IO operation definition."""
        result = self._operation.get_results()
        if self._operation.name == EVAL_IO_SIGNATURE[0]:
            # Special treatment: Exchange result arg with one with the correct type.
            result = result[:]
            result_var = copy.copy(result[0])
            target = self._translator.get_target(self._node.args[1], self._ctx)
            if target.type.name != 'Callable':
                result_var.type = target.type
            result[0] = result_var
        return result

    @property
    def _result_instances(self) -> List[ast.expr]:
        """Return results as given in IO operation call."""
        parameters_count = len(self._operation.get_parameters())
        return self._node.args[parameters_count:]

    def translate(self) -> List[Expr]:
        """Translate variables bound by IO operation call."""
        assert not self._equations, "translate is called twice."

        self._check()
        contexts = self._create_result_contexts()

        for result in contexts:
            if not isinstance(result.instance, ast.Name):
                raise_invalid_operation_use(
                    'not_variable_in_result_position', self._node)
            else:
                result.getter = self._translator.create_result_getter(
                    self._node, result.definition, self._ctx)
                self._set_variable(result)

                if self._io_ctx.contains_variable(result.var_name):
                    # Variable denotes a result of the operation being opened.
                    self._handle_opener_result_var(result)
                elif isinstance(result.var, PythonIOExistentialVar):
                    self._handle_existential_var(result)
                else:
                    # Normal variable, which is already defined.
                    self._handle_normal_var(result)

        return self._equations

    def _check(self) -> None:
        """Perform some well-formedness checks."""
        if len(self._result_definitions) != len(self._result_instances):
            raise_invalid_operation_use('result_mismatch', self._node)

    def _create_result_contexts(self) -> List[IOOperationResult]:
        contexts = [
            IOOperationResult(self._node, definition, instance)
            for definition, instance in zip(
                self._result_definitions, self._result_instances)
        ]
        return contexts

    def _add_equation(self, result: IOOperationResult) -> None:
        equation = self._viper.EqCmp(result.getter,
                                     result.var.ref(result.node, self._ctx),
                                     self._position, self._info)
        self._equations.append(equation)

    def _set_variable(self, result: IOOperationResult) -> None:
        instance = cast(ast.Name, result.instance)
        var_name = instance.id
        result.var_name = var_name
        if var_name in self._ctx.var_aliases:
            result.var = self._ctx.var_aliases[var_name]
        else:
            result.var = self._ctx.actual_function.get_variable(var_name)

    def _handle_opener_result_var(
            self, result: IOOperationResult) -> None:
        assert isinstance(result.var, PythonVar)
        if self._io_ctx.is_variable_defined(result.var_name):
            self._add_equation(result)
        else:
            self._io_ctx.define_variable(result.var_name, result.getter)

    def _handle_existential_var(
            self, result: IOOperationResult) -> None:
        assert isinstance(result.var, PythonIOExistentialVar)
        if result.var.is_defined():
            self._add_equation(result)
        else:
            getter = result.getter
            old_getter = self._viper.Old(getter, getter.pos(), getter.info())
            result.var.set_ref(getter, old_getter)

    def _handle_normal_var(self, result: IOOperationResult) -> None:
        assert isinstance(result.var, (PythonVar, PythonGlobalVar))
        self._add_equation(result)
