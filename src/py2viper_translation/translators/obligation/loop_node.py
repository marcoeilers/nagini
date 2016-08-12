"""Code for constructing Silver while node with obligation stuff."""


import ast

from typing import List, Union

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.config import obligation_config
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import rules
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    VarDecl,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)
from py2viper_translation.translators.obligation.obligation_info import (
    PythonLoopObligationInfo,
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

    def prepend_invariants(self, invariants) -> None:
        """Prepend ``invariants`` to the invariants list."""
        self.invariants[0:0] = invariants

    def append_invariant(self, invariant) -> None:
        """Append ``invariant`` to the invariants list."""
        self.invariants.append(invariant)

    def prepend_body(self, statements) -> None:
        """Prepend ``statements`` to body."""
        self.body[0:0] = statements

    def append_body(self, statement) -> None:
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
        self._add_method_measure_map_preserved_invariant()
        self._add_leak_check()
        self._set_up_measures()
        self._save_must_terminate_amount(
            self._loop_obligation_info.original_must_terminate_var)
        self._save_loop_termination()
        self._set_loop_check_before()
        self._check_loop_promises_terminate()
        self._set_loop_check_after_body()
        self._check_loop_preserves_termination()
        self._add_loop()
        self._reset_must_terminate(
            self._loop_obligation_info.original_must_terminate_var)

    def _add_method_measure_map_preserved_invariant(self) -> None:
        """Add invariant that method measure map is not changed."""
        if obligation_config.disable_measures:
            return
        measure_map = self._method_measure_map
        permission = measure_map.get_contents_access()
        assertion = measure_map.get_contents_preserved_assertion()
        self._obligation_loop.prepend_invariants([
            permission.translate(
                self._translator, self._ctx, self._position, self._info),
            assertion.translate(
                self._translator, self._ctx, self._position, self._info),
        ])

    def _add_leak_check(self) -> None:
        """Add leak checks to invariant."""
        reference_name = self._ctx.actual_function.get_fresh_name('_r')
        leak_check = self._obligation_manager.create_leak_check(reference_name)
        loop_check_before = expr.BoolVar(
            self._loop_obligation_info.loop_check_before_var)
        termination_flag = expr.BoolVar(
            self._loop_obligation_info.termination_flag_var)

        if (not obligation_config.disable_loop_context_leak_check and
                not self._loop_obligation_info.always_terminates()):
            before_loop_leak_check = expr.InhaleExhale(
                expr.TrueLit(),
                expr.Implies(
                    loop_check_before,
                    expr.Implies(expr.Not(termination_flag), leak_check)))
            info = self._to_info('Leak check for context.')
            position = self._to_position(
                conversion_rules=rules.OBLIGATION_LOOP_CONTEXT_LEAK_CHECK_FAIL)
            self._obligation_loop.append_invariant(
                before_loop_leak_check.translate(
                    self._translator, self._ctx, position, info))

        if not obligation_config.disable_loop_body_leak_check:
            body_leak_check = expr.InhaleExhale(
                expr.TrueLit(),
                expr.Implies(expr.Not(loop_check_before), leak_check))
            info = self._to_info('Leak check for loop body.')
            position = self._to_position(
                conversion_rules=rules.OBLIGATION_LOOP_BODY_LEAK_CHECK_FAIL)
            self._obligation_loop.append_invariant(
                body_leak_check.translate(
                    self._translator, self._ctx, position, info))

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
        # Add access permission to invariant.
        loop_check_before = expr.BoolVar(
            self._loop_obligation_info.loop_check_before_var)
        permission = loop_measure_map.get_contents_access()
        invariant = expr.Implies(expr.Not(loop_check_before), permission)
        self._obligation_loop.prepend_invariants([
            invariant.translate(
                self._translator, self._ctx, self._position, self._info),
        ])

    def _save_loop_termination(self) -> None:
        """Save if loop promises to terminate into a variable."""
        if obligation_config.disable_termination_check:
            return
        instances = self._loop_obligation_info.get_instances(
            self._obligation_manager.must_terminate_obligation.identifier())
        disjuncts = [
            instance.create_guard_expression()
            for instance in instances]
        assign = expr.Assign(
            self._loop_obligation_info.termination_flag_var,
            expr.BigOr(disjuncts))
        info = self._to_info('Save loop termination promise.')
        self._append_statement(assign, info=info)

    def _set_loop_check_before(self) -> None:
        """Set the variable indicating that we are before loop."""
        assign = expr.Assign(
            self._loop_obligation_info.loop_check_before_var,
            expr.TrueLit())
        info = self._to_info('We are before loop.')
        self._append_statement(assign, info=info)

    def _check_loop_promises_terminate(self) -> None:
        """Check that loop promises to terminate if it has to."""
        if obligation_config.disable_termination_check:
            return
        predicate = self._get_must_terminate_predicate()
        check = expr.Implies(
            expr.CurrentPerm(predicate) > expr.NoPerm(),
            expr.BigOr([
                expr.BoolVar(self._loop_obligation_info.termination_flag_var),
                expr.Not(self._loop_obligation_info.construct_loop_condition())
            ])
        )
        info = self._to_info('Check if loop terminates.')
        position = self._to_position(
            conversion_rules=rules.OBLIGATION_LOOP_TERMINATION_PROMISE_MISSING)
        self._append_statement(expr.Assert(check), position, info)

    def _set_loop_check_after_body(self) -> None:
        """Set the variable indicating that we are after loop body."""
        assign = expr.Assign(
            self._loop_obligation_info.loop_check_before_var,
            expr.FalseLit())
        info = self._to_info('We are after loop body.')
        statement = assign.translate(
            self._translator, self._ctx, self._position, info)
        self._obligation_loop.append_body(statement)

    def _check_loop_preserves_termination(self) -> None:
        """Check that loop keeps the promise to terminate."""
        if obligation_config.disable_termination_check:
            return
        instances = self._loop_obligation_info.get_instances(
            self._obligation_manager.must_terminate_obligation.identifier())
        disjuncts = [
            expr.Not(self._loop_obligation_info.construct_loop_condition())]
        for instance in instances:
            guard = instance.create_guard_expression()
            measure_check = self._loop_obligation_info.loop_measure_map.check(
                expr.VarRef(self._obligation_info.current_thread_var),
                instance.obligation_instance.get_measure())
            disjuncts.append(expr.BigAnd([guard, measure_check]))
        check = expr.Implies(
            expr.BoolVar(self._loop_obligation_info.termination_flag_var),
            expr.BigOr(disjuncts))
        assertion = expr.Assert(check)
        position = self._to_position(
            conversion_rules=rules.OBLIGATION_LOOP_TERMINATION_PROMISE_FAIL)
        info = self._to_info('Check if loop continues to terminate.')
        statement = assertion.translate(
            self._translator, self._ctx, position, info)
        self._obligation_loop.append_body(statement)

    def _add_loop(self) -> None:
        """Add the actual loop node."""
        body_block = self._translator.translate_block(
            self._obligation_loop.body, self._position, self._info)
        loop = self._viper.While(
            self._obligation_loop.condition, self._obligation_loop.invariants,
            self._obligation_loop.local_vars, body_block,
            self._position, self._info)
        self._statements.append(loop)

    @property
    def _loop_obligation_info(self) -> PythonLoopObligationInfo:
        return self._ctx.obligation_context.current_loop_info
