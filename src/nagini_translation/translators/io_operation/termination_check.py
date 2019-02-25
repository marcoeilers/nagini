"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""IO operation termination checks."""


import ast

from typing import List

from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import Rules, rules
from nagini_translation.lib.guard_collectors import (
    GuardCollectingVisitor,
)
from nagini_translation.lib.program_nodes import PythonIOOperation
from nagini_translation.lib.typedefs import (
    Expr,
    Stmt,
)
from nagini_translation.lib.util import (
    join_expressions,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.io_operation.common import (
    IOOperationCommonTranslator,
)


class TerminationCheckGenerator(GuardCollectingVisitor):
    """Class responsible for generating IO operation termination checks."""

    def __init__(self, io_translator: IOOperationCommonTranslator,
                 ctx: Context,
                 termination_condition: Expr,
                 termination_measure: Expr,
                 termination_measure_node: ast.AST) -> None:
        super().__init__()
        self._io_translator = io_translator
        self._ctx = ctx
        self._termination_condition = termination_condition
        self._termination_measure = termination_measure
        self._termination_measure_node = termination_measure_node
        self._current_operation = None          # type: PythonIOOperation
        self._current_operation_node = None     # type: ast.Call
        self._current_identifier = None         # type: str
        self._current_guard_condition = None    # type: Expr
        self._checks = []                       # type: List[Stmt]

    def create_checks(self, node: Expr = None) -> List[Stmt]:
        """Create assertions that check termination."""
        self._check_termination_measure_positive()
        if node is not None:
            self.traverse(node)
        return self._checks

    def _is_io_operation(self, node: ast.Call) -> bool:
        return isinstance(self._io_translator.get_target(node, self._ctx),
                          PythonIOOperation)

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_io_operation(node):
            self._create_termination_checks(node)
        else:
            super().visit_Call(node)

    def _create_termination_checks(self, node: ast.Call) -> None:
        """Create termination checks for sub-operation."""
        assert self._current_operation is None
        assert self._current_identifier is None
        assert self._current_guard_condition is None
        assert self._current_operation_node is None

        self._current_operation_node = node

        operation = self._io_translator.get_target(node, self._ctx)
        self._current_operation = operation

        identifier = "{} ({}:{})".format(
            operation.name, node.lineno, node.col_offset)
        self._current_identifier = identifier

        self._current_guard_condition = self._create_guard_condition()

        self._check_gap()
        with self._ctx.aliases_context():
            self._io_translator.set_up_io_operation_input_aliases(
                self._current_operation, node, self._ctx)
            self._check_termination_condition()
            self._check_termination_measure()

        self._current_operation = None
        self._current_identifier = None
        self._current_guard_condition = None
        self._current_operation_node = None

    def _create_guard_condition(self) -> Expr:
        """Generate a Silver expression that guards current AST node."""
        guard_sil_parts = []
        for part in self.current_guard:
            sil_part = self._translate_expr(part, target_type=self._viper.Bool)
            guard_sil_parts.append(sil_part)
        and_operator = (
            lambda left, right:
            self._viper.And(left, right,
                            self._position(), self._no_info()))
        condition = join_expressions(
            and_operator, [self._termination_condition] + guard_sil_parts)
        return condition

    def _add_check(self, condition: Expr, comment_template: str,
                   position: 'viper_ast.IdentifierPosition') -> None:
        check = self._viper.Implies(
            self._current_guard_condition, condition,
            position, self._no_info())
        comment = comment_template.format(self._current_identifier)
        assertion = self._viper.Assert(
            check, position, self._to_info(comment))
        self._checks.append(assertion)

    def _check_termination_measure_positive(self) -> None:
        """Check that termination measure is positive."""
        self._current_guard_condition = self._termination_condition
        self._current_operation_node = self._termination_measure_node

        position = self._position(
            rules.TERMINATION_CHECK_MEASURE_NON_POSITIVE)
        positive = self._viper.GtCmp(
            self._termination_measure,
            self._viper.IntLit(0, position, self._no_info()),
            position, self._no_info())
        self._add_check(positive, "Termination measure must be positive.",
                        position)

        self._current_guard_condition = None
        self._current_operation_node = None

    def _check_gap(self) -> None:
        """Check that ``gap_io`` is disabled under termination condition."""
        if self._current_operation.name == 'gap_io':
            position = self._position(
                rules.TERMINATION_CHECK_GAP_ENABLED)
            false = self._viper.FalseLit(position, self._no_info())
            self._add_check(false, "Gap at {}.", position)

    def _check_termination_condition(self) -> None:
        """Check that child termination condition is implied."""
        termination_condition = self._translate_expr(
            self._current_operation.get_terminates(),
            target_type=self._viper.Bool)
        position = self._position(
            rules.TERMINATION_CHECK_CHILD_TERMINATION_NOT_IMPLIED)
        self._add_check(termination_condition,
                        "Termination condition of {}.",
                        position)

    def _check_termination_measure(self) -> None:
        """Check that child measure is strictly smaller."""
        termination_measure = self._translate_expr(
            self._current_operation.get_termination_measure(),
            target_type=self._viper.Int)
        position = self._position(
            rules.TERMINATION_CHECK_MEASURE_NON_DECREASING)
        larger = self._viper.GtCmp(
            self._termination_measure,
            termination_measure,
            position, self._no_info())
        self._add_check(larger, "Termination measure of {}.", position)

    def _translate_expr(self, node: ast.AST, target_type=None) -> Expr:
        statement, expression = self._io_translator.translate_expr(
            node, self._ctx, target_type=target_type)
        assert not statement
        return expression

    def _no_info(self) -> 'viper_ast.NoInfo':
        return self._io_translator.no_info(self._ctx)

    def _to_info(self, comment) -> 'viper_ast.SimpleInfo':
        return self._io_translator.to_info([comment], self._ctx)

    def _position(
            self,
            conversion_rules: Rules=None) -> 'viper_ast.IdentifierPosition':
        return self._io_translator.to_position(
            self._current_operation_node, self._ctx, rules=conversion_rules)

    @property
    def _viper(self) -> ViperAST:
        return self._io_translator.viper
