"""Code for constructing Silver Method call node with obligation stuff."""


import ast

from typing import List, Optional

from py2viper_translation.lib.config import obligation_config
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)


class ObligationMethodCall:
    """Info for generating Silver ``MethodCall`` AST node."""

    def __init__(
            self, name: str, args: List[Expr], targets: List[Expr]) -> None:
        self.name = name
        self.original_args = args[:]
        self.args = args
        self.targets = targets

    def prepend_arg(self, arg: Expr) -> None:
        """Prepend ``args`` to the argument list."""
        self.args.insert(0, arg)


class ObligationMethodCallNodeConstructor(StatementNodeConstructorBase):
    """A class that creates a method call node with obligation stuff."""

    def __init__(
            self, obligation_method_call: ObligationMethodCall,
            position: Position, info: Info,
            translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager,
            target_method: Optional[PythonMethod],
            target_node: Optional[ast.AST]) -> None:
        """Constructor.

        If ``target_node`` is ``None``, then:

        1.  It is assumed that we are translating a behavioural
            subtyping check.
        2.  ``target_method.node`` is used for computing default
            position.
        """
        super().__init__(
            translator, ctx, obligation_manager, position, info,
            target_node or target_method.node)
        self._obligation_method_call = obligation_method_call
        self._target_method = target_method
        self._target_node = target_node

    def construct_call(self) -> None:
        """Construct statements to perform a call."""
        self._add_aditional_arguments()
        self._add_call()

    def _add_aditional_arguments(self) -> None:
        """Add current thread and caller measure map arguments."""
        if not obligation_config.disable_measures:
            self._obligation_method_call.prepend_arg(
                self._obligation_info.method_measure_map.get_var().ref(
                    self._target_node, self._ctx))
        self._obligation_method_call.prepend_arg(
            self._obligation_info.current_thread_var.ref(
                self._target_node, self._ctx))

    def _add_call(self) -> None:
        """Add the actual call node."""
        call = self._obligation_method_call
        statement = self._viper.MethodCall(
            call.name, call.args, call.targets,
            self._position, self._info)
        self._statements.append(statement)