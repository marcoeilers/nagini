"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Obligation translator in loops."""


import ast

from typing import List, Union

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import (
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    VarDecl,
)
from nagini_translation.translators.obligation.common import (
    CommonObligationTranslator
)
from nagini_translation.translators.obligation.loop_node import (
    ObligationLoop,
    ObligationLoopNodeConstructor,
)
from nagini_translation.translators.obligation.types.base import (
    ObligationInstance,
)
from nagini_translation.translators.obligation.obligation_info import (
    BaseObligationInfo,
    PythonLoopObligationInfo,
)


class LoopObligationTranslator(CommonObligationTranslator):
    """Class for translating obligations in loops."""

    def enter_loop_translation(
            self, node: Union[ast.While, ast.For], ctx: Context,
            err_var: PythonVar = None) -> None:
        """Update context with info needed to translate loop."""
        info = PythonLoopObligationInfo(
            self._obligation_manager, node, self, ctx.actual_function,
            err_var)
        info.traverse_invariants()
        ctx.obligation_context.push_loop_info(info)

    def leave_loop_translation(self, ctx: Context) -> None:
        """Remove loop translation info from context."""
        ctx.obligation_context.pop_loop_info()

    def _get_obligation_info(self, ctx: Context) -> BaseObligationInfo:
        return ctx.obligation_context.current_loop_info

    def _create_obligation_instance_use(
            self, obligation_instance: ObligationInstance,
            ctx: Context) -> sil.InhaleExhale:
        return obligation_instance.get_use_loop(ctx)

    def create_while_node(
            self, ctx: Context, cond: Expr,
            invariants: List[Expr],
            local_vars: List[VarDecl],
            body: List[Stmt], node: Union[ast.While, ast.For]) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        obligation_loop = ObligationLoop(cond, invariants, local_vars, body)
        constructor = ObligationLoopNodeConstructor(
            obligation_loop, node, self, ctx, self._obligation_manager)
        constructor.construct_loop()
        return constructor.get_statements()
