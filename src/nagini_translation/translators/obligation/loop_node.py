"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Code for constructing Silver while node with obligation stuff."""


import ast
from typing import List, Union

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import rules
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
    VarDecl,
)
from nagini_translation.sif.lib.viper_ast_extended import ViperASTExtended
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)
from nagini_translation.translators.obligation.obligation_info import (
    PythonLoopObligationInfo,
)
from nagini_translation.translators.obligation.utils import (
    bound_obligations,
)


class ObligationLoop:
    """Info for generating Silver ``While`` AST node."""

    def __init__(
            self, condition: Expr, invariants: List[Expr],
            local_vars: List[VarDecl], body: List[Stmt]) -> None:
        self.condition = condition
        self.invariants = invariants
        self.local_vars = local_vars
        self.body = body

    def prepend_invariant(self, invariant: Expr) -> None:
        """Prepend ``invariant`` to the invariants list."""
        self.invariants.insert(0, invariant)

    def append_invariants(self, invariants: List[Expr]) -> None:
        """Append ``invariants`` to the invariants list."""
        self.invariants.extend(invariants)

    def prepend_body(self, statements: List[Stmt]) -> None:
        """Prepend ``statements`` to body."""
        self.body[0:0] = statements

    def append_body(self, statement: Stmt) -> None:
        """Append ``statement`` to body."""
        self.body.append(statement)


class ObligationLoopNodeConstructor(StatementNodeConstructorBase):
    """A class that creates a while loop node with obligation stuff."""

    def __init__(
            self, obligation_loop: ObligationLoop,
            node: Union[ast.While, ast.For],
            translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager) -> None:
        position = translator.to_position(node, ctx)
        info = translator.no_info(ctx)
        super().__init__(
            translator, ctx, obligation_manager, position, info, node)
        self._obligation_loop = obligation_loop
        self._node = node

    def get_statements(self) -> List[Stmt]:
        """Get all generated statements."""
        return self._statements

    def construct_loop(self) -> None:
        """Construct statements to perform a loop."""
        self._add_current_wait_level()
        self._add_additional_invariants()
        self._add_leak_check()
        self._set_up_measures()
        self._bound_obligations()
        self._save_must_terminate_amount(
            self._loop_obligation_info.original_must_terminate_var)
        self._save_loop_termination()
        self._set_loop_check_before()
        self._set_loop_check_after_body()
        self._check_loop_preserves_termination()
        self._prepend_loop_body()
        self._add_loop()
        self._add_additional_statements_after_loop()
        self._reset_must_terminate(
            self._loop_obligation_info.original_must_terminate_var)

    def _add_current_wait_level(self) -> None:
        """Inhale assumptions about current wait-level variable."""
        if obligation_config.disable_waitlevel_check:
            return
        context_info = self._ctx.obligation_context.get_surrounding_loop_info()
        if context_info:
            context_residue_level = context_info.residue_level
        else:
            method_info = self._ctx.current_function.obligation_info
            context_residue_level = method_info.residue_level
        invariant = self._translator.initialize_current_wait_level(
            sil.PermVar(self._loop_obligation_info.residue_level),
            sil.PermVar(context_residue_level),
            self._ctx)
        translated = invariant.translate(
            self._translator, self._ctx, self._position, self._info)
        self._obligation_loop.prepend_invariant(translated)

    def _add_additional_invariants(self) -> None:
        """Add additional invariants from the obligation info."""
        self._obligation_loop.append_invariants(
            self._loop_obligation_info.get_additional_invariants())

    def _add_leak_check(self) -> None:
        """Add leak checks to invariant."""
        reference_name = self._ctx.actual_function.get_fresh_name('_r')
        leak_check = self._obligation_manager.create_leak_check(reference_name)
        loop_check_before = sil.BoolVar(
            self._loop_obligation_info.loop_check_before_var)
        termination_flag = sil.BoolVar(
            self._loop_obligation_info.termination_flag_var)

        if not obligation_config.disable_loop_context_leak_check:
            must_terminate = self._obligation_manager.must_terminate_obligation
            predicate = must_terminate.create_predicate_access(
                self._obligation_info.current_thread_var)
            termination_leak_check = sil.CurrentPerm(predicate) == sil.NoPerm()
            loop_cond = self._loop_obligation_info.construct_loop_condition()
            before_loop_leak_check = sil.InhaleExhale(
                sil.TrueLit(),
                sil.Implies(
                    loop_check_before,
                    sil.BigOr([
                        termination_flag,
                        sil.Not(loop_cond),
                        sil.BigAnd([termination_leak_check, leak_check])
                    ])
                )
            )
            info = self._to_info('Leak check for context.')
            position = self._to_position(
                conversion_rules=rules.OBLIGATION_LOOP_CONTEXT_LEAK_CHECK_FAIL)
            self._obligation_loop.append_invariants([
                before_loop_leak_check.translate(
                    self._translator, self._ctx, position, info)])

        if not obligation_config.disable_loop_body_leak_check:
            body_leak_check = sil.InhaleExhale(
                sil.TrueLit(),
                sil.Implies(sil.Not(loop_check_before), leak_check))
            info = self._to_info('Leak check for loop body.')
            position = self._to_position(
                conversion_rules=rules.OBLIGATION_LOOP_BODY_LEAK_CHECK_FAIL)
            self._obligation_loop.append_invariants([
                body_leak_check.translate(
                    self._translator, self._ctx, position, info)])

    def _set_up_measures(self) -> None:
        """Create and initialize loop's measure map."""
        if obligation_config.disable_measures:
            return
        # Set up measures.
        loop_measure_map = self._loop_obligation_info.loop_measure_map
        instances = self._loop_obligation_info.get_all_instances()
        statements = loop_measure_map.initialize(
            instances, self._translator, self._ctx)
        self._obligation_loop.prepend_body(statements)

    def _bound_obligations(self) -> None:
        """Convert all unbounded obligations to bounded ones."""
        statements = bound_obligations(
            self._loop_obligation_info.get_all_instances(),
            self._translator, self._ctx, self._position, self._info)
        self._obligation_loop.prepend_body(statements)

    def _save_loop_termination(self) -> None:
        """Save if loop promises to terminate into a variable."""
        if obligation_config.disable_termination_check:
            return
        assign = sil.Assign(
            self._loop_obligation_info.termination_flag_var,
            self._loop_obligation_info.create_termination_check(True))
        info = self._to_info('Save loop termination promise.')
        self._append_statement(assign, info=info)

    def _set_loop_check_before(self) -> None:
        """Set the variable indicating that we are before loop."""
        if obligation_config.disable_all:
            return
        assign = sil.Assign(
            self._loop_obligation_info.loop_check_before_var,
            sil.TrueLit())
        info = self._to_info('We are before loop.')
        self._append_statement(assign, info=info)

    def _set_loop_check_after_body(self) -> None:
        """Set the variable indicating that we are after loop body."""
        if obligation_config.disable_all:
            return
        assign = sil.Assign(
            self._loop_obligation_info.loop_check_before_var,
            sil.FalseLit())
        info = self._to_info('We are after loop body.')
        statement = assign.translate(
            self._translator, self._ctx, self._position, info)
        self._obligation_loop.append_body(statement)

    def _check_loop_preserves_termination(self) -> None:
        """Check that loop keeps the promise to terminate."""
        if obligation_config.disable_termination_check:
            return
        check = sil.Implies(
            sil.BoolVar(self._loop_obligation_info.termination_flag_var),
            sil.BigOr([
                sil.Not(self._loop_obligation_info.construct_loop_condition()),
                self._loop_obligation_info.create_termination_check(False)
            ])
        )
        assertion = sil.Assert(check)
        position = self._to_position(
            conversion_rules=rules.OBLIGATION_LOOP_TERMINATION_PROMISE_FAIL)
        comment = 'Check if loop continues to terminate.'
        if isinstance(self._viper, ViperASTExtended):
            info = self._viper.SIFInfo([comment], continue_unaware=True)
        else:
            info = self._to_info(comment)
        statement = assertion.translate(
            self._translator, self._ctx, position, info)
        self._obligation_loop.append_body(statement)

    def _prepend_loop_body(self) -> None:
        """Add additional statements before loop from the obligation info."""
        self._obligation_loop.prepend_body(
            self._loop_obligation_info.get_prepend_body())

    def _add_loop(self) -> None:
        """Add the actual loop node."""
        body_block = self._translator.translate_block(
            self._obligation_loop.body, self._position, self._info)
        loop = self._viper.While(
            self._obligation_loop.condition, self._obligation_loop.invariants,
            self._obligation_loop.local_vars, body_block,
            self._position, self._info)
        self._statements.append(loop)

    def _add_additional_statements_after_loop(self) -> None:
        """Add additional statements after loop from the obligation info."""
        self._statements.extend(
            self._loop_obligation_info.get_after_loop())

    @property
    def _loop_obligation_info(self) -> PythonLoopObligationInfo:
        return self._ctx.obligation_context.current_loop_info
