"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Common code for constructing Silver nodes with obligation stuff."""


import ast

from typing import List, Union

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.errors import Rules
from nagini_translation.lib.program_nodes import (
    PythonVar,
)
from nagini_translation.lib.typedefs import (
    Info,
    Stmt,
    Position,
)
from nagini_translation.lib.util import (
    pprint,
)
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.measures import (
    MeasureMap,
)
from nagini_translation.translators.obligation.types import (
    must_terminate,
)
from nagini_translation.translators.obligation.obligation_info import (
    PythonMethodObligationInfo,
)


class StatementNodeConstructorBase:
    """Common functionality for loop and method call constructors."""

    def __init__(
            self, translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager,
            position: Position, info: Info,
            default_position_node: ast.AST) -> None:
        self._position = position
        """Default position."""
        self._info = info
        """Default info."""
        self._translator = translator
        self._ctx = ctx
        self._obligation_manager = obligation_manager
        self._default_position_node = default_position_node
        self._statements = []

    def get_statements(self) -> List[Stmt]:
        """Get all generated statements."""
        return self._statements

    def _save_must_terminate_amount(
            self, amount_var: PythonVar) -> None:
        """Save the current permission amount to a variable."""
        if obligation_config.disable_termination_check:
            return
        predicate = self._get_must_terminate_predicate()
        assign = sil.Assign(amount_var, sil.CurrentPerm(predicate))
        info = self._to_info('Save current MustTerminate amount.')
        self._append_statement(assign, info=info)

    def _reset_must_terminate(self, amount_var: PythonVar) -> None:
        """Reset ``MustTerminate`` permission to its original level.

        .. note::

            Implication is needed because in Silicon if callee took all
            permission, the ``exhale acc(..., none)`` would fail, even
            though this exhale does nothing.
        """
        if obligation_config.disable_termination_check:
            return
        predicate = self._get_must_terminate_predicate()
        original_amount = sil.PermVar(amount_var)
        perm = sil.CurrentPerm(predicate) - original_amount
        exhale = sil.Exhale(sil.Implies(
            sil.CurrentPerm(predicate) > sil.NoPerm(),
            sil.Acc(predicate, perm)))
        info = self._to_info('Reset MustTerminate amount to original level.')
        self._append_statement(exhale, info=info)

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper

    @property
    def _must_terminate(self) -> must_terminate.MustTerminateObligation:
        return self._obligation_manager.must_terminate_obligation

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        """Get the surrounding method obligation info."""
        return self._ctx.current_function.obligation_info

    @property
    def _method_measure_map(self) -> MeasureMap:
        """Get the surrounding method measure map."""
        return self._obligation_info.method_measure_map

    def _get_must_terminate_predicate(self) -> sil.PredicateAccess:
        cthread = self._obligation_info.current_thread_var
        return self._must_terminate.create_predicate_access(cthread)

    def _to_position(
            self, node: ast.AST = None,
            conversion_rules: Rules = None,
            error_node: Union[str, ast.AST] = None) -> Position:
        error_string = None
        if error_node is not None:
            if isinstance(error_node, ast.AST):
                error_string = pprint(error_node)
            else:
                error_string = error_node
        return self._translator.to_position(
            node or self._default_position_node, self._ctx,
            error_string=error_string, rules=conversion_rules)

    def _to_info(self, template, *args, **kwargs) -> Info:
        return self._translator.to_info(
            [template.format(*args, **kwargs)], self._ctx)

    def _append_statement(
            self, statement: sil.Statement,
            position: Position = None, info: Info = None) -> None:
        translated = statement.translate(
            self._translator, self._ctx,
            position or self._position,
            info or self._info)
        self._statements.append(translated)
