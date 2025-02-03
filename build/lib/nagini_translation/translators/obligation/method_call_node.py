"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Code for constructing Silver Method call node with obligation stuff."""


import ast

from typing import List, Optional

from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonMethod,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)


class ObligationMethodCall:
    """Info for generating Silver ``MethodCall`` AST node."""

    def __init__(
            self, name: str, args: List[Expr], targets: List[Expr]) -> None:
        assert name
        assert all(args)
        assert all(targets)
        self.name = name
        self.original_args = args[:]
        self.args = args
        self.targets = targets

    def prepend_arg(self, arg: Expr) -> None:
        """Prepend ``args`` to the argument list."""
        assert arg
        self.args.insert(0, arg)

    def prepend_target(self, target: Expr) -> None:
        """Prepend ``target`` to the target list."""
        assert target
        self.targets.insert(0, target)


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
        self._add_additional_arguments()
        self._add_additional_targets()
        self._add_call()

    def _add_additional_arguments(self) -> None:
        """Add current thread and caller measure map arguments."""
        if obligation_config.disable_all:
            return
        if self._ctx.obligation_context.is_translating_loop():
            loop_info = self._ctx.obligation_context.current_loop_info
            residue_level = loop_info.residue_level
        else:
            residue_level = self._obligation_info.residue_level
        self._obligation_method_call.prepend_arg(
            residue_level.ref(self._target_node, self._ctx))
        if not obligation_config.disable_measures:
            self._obligation_method_call.prepend_arg(
                self._obligation_info.method_measure_map.get_var().ref(
                    self._target_node, self._ctx))
        self._obligation_method_call.prepend_arg(
            self._obligation_info.current_thread_var.ref(
                self._target_node, self._ctx))

    def _add_additional_targets(self) -> None:
        """Add current wait level dummy target."""
        if obligation_config.disable_waitlevel_check:
            return
        self._obligation_method_call.prepend_target(
            self._obligation_info.current_wait_level_target.ref())

    def _add_call(self) -> None:
        """Add the actual call node."""
        call = self._obligation_method_call
        statement = self._viper.MethodCall(
            call.name, call.args, call.targets,
            self._position, self._info)
        self._statements.append(statement)
