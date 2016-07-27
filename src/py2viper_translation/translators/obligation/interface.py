"""Public interface to obligation translator."""


import ast

from typing import List, Tuple

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.typedefs import (
    Field,
    Method,
    Predicate,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.util import (
    get_func_name,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.obligation.loop import (
    LoopObligationTranslator,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.method import (
    MethodObligationTranslator,
)
from py2viper_translation.translators.obligation.visitors import (
    PythonMethodObligationInfo,
)


class ObligationTranslator(CommonTranslator):
    """Translator for obligations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._obligation_manager = ObligationManager()
        self._method_translator = MethodObligationTranslator(
            *args, **kwargs)
        self._loop_translator = LoopObligationTranslator(
            *args, **kwargs)

    def enter_loop_translation(self, node, ctx) -> None:
        """Update context with info needed to translate loop."""
        self._loop_translator.enter_loop_translation(node, ctx)

    def leave_loop_translation(self, ctx) -> None:
        """Remove loop translation info from context."""
        self._loop_translator.leave_loop_translation(ctx)

    def create_while_node(self, *args, **kwargs) -> List[Stmt]:
        """Construct a while loop AST node with obligation stuff."""
        return self._loop_translator.create_while_node(*args, **kwargs)

    def translate_obligation_contractfunc_call(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to obligation contract function."""
        func_name = get_func_name(node)
        if func_name == 'MustTerminate':
            return self._translate_must_terminate(node, ctx)
        else:
            raise UnsupportedException(
                node, 'Unsupported contract function.')

    def _translate_must_terminate(
            self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """Translate a call to ``MustTerminate``."""
        if ctx.obligation_context.is_translating_loop():
            return self._loop_translator.translate_must_terminate(node, ctx)
        elif ctx.obligation_context.is_translating_posts:
            raise InvalidProgramException(
                node, 'obligation.must_terminate.in_postcondition')
        else:
            return self._method_translator.translate_must_terminate(node, ctx)

    def get_obligation_preamble(
            self,
            ctx: Context) -> Tuple[List[Predicate], List[Field]]:
        """Construct obligation preamble."""
        predicates = self._obligation_manager.create_predicates(self)
        return predicates, []

    def create_method_node(self, *args, **kwargs) -> Method:
        """Construct method AST node with additional obligation stuff."""
        return self._method_translator.create_method_node(*args, **kwargs)

    def create_method_call_node(self, *args, **kwargs) -> List[Stmt]:
        """Construct a method call AST node with obligation stuff."""
        return self._method_translator.create_method_call_node(
            *args, **kwargs)

    def create_obligation_info(self, method: PythonMethod) -> object:
        """Create obligation info for the method."""
        info = PythonMethodObligationInfo(
            self._obligation_manager, method, self.translator)
        info.traverse_preconditions()
        info.traverse_postconditions()
        return info
