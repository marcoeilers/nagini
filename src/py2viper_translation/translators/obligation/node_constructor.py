"""Common code for constructing Silver nodes with obligation stuff."""


import ast

from typing import List, Union

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules
from py2viper_translation.lib.typedefs import (
    Info,
    Stmt,
    Position,
)
from py2viper_translation.lib.util import (
    pprint,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.measures import (
    MeasureMap,
)
from py2viper_translation.translators.obligation.types import (
    must_terminate,
)
from py2viper_translation.translators.obligation.obligation_info import (
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

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper

    @property
    def _must_terminate(self) -> must_terminate.MustTerminateObligation:
        return self._obligation_manager.must_terminate_obligation

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        """Get the surrounding method obligation info."""
        return self._ctx.actual_function.obligation_info

    @property
    def _method_measure_map(self) -> MeasureMap:
        """Get the surrounding method measure map."""
        return self._obligation_info.method_measure_map

    def _get_must_terminate_predicate(self) -> expr.Predicate:
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
            self, statement: expr.Statement,
            position: Position = None, info: Info = None) -> None:
        translated = statement.translate(
            self._translator, self._ctx,
            position or self._position,
            info or self._info)
        self._statements.append(translated)
