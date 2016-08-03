"""Code for constructing Silver Method call node with obligation stuff."""


import ast

from typing import List

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Stmt,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.obligation.visitors import (
    PythonMethodObligationInfo,
)


class ObligationsMethodCallNodeConstructor:
    """A class that creates a method call node with obligation stuff."""

    def __init__(
            self, method_name: str, args, targets, position, info,
            translator: 'AbstractTranslator', ctx: Context,
            target_method: PythonMethod = None,
            target_node: ast.AST = None) -> None:
        self._method_name = method_name
        self._args = args
        self._targets = targets
        self._position = position
        self._info = info
        self._translator = translator
        self._ctx = ctx
        self._method = target_method
        self._node = target_node
        self._statements = []

    def get_statements(self) -> List[Stmt]:
        """Get all generated statements."""
        return self._statements

    def construct_call(self) -> None:
        """Construct statements to perform a call."""
        self._add_aditional_arguments()
        self._add_call()
        # TODO: Finish implementation.

    def _add_aditional_arguments(self) -> None:
        args = [
            self._obligation_info.current_thread_var.ref(
                self._node, self._ctx),
            self._obligation_info.method_measure_map.get_var().ref(
                self._node, self._ctx),
        ]
        self._args = args + self._args

    def _add_call(self) -> None:
        call = self._viper.MethodCall(
            self._method_name, self._args, self._targets,
            self._position, self._info)
        self._statements.append(call)

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        return self._method.obligation_info

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper
