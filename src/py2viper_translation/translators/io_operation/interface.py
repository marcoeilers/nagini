"""Public interface to IO operation translator."""


import ast

from typing import List, Tuple

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
)
from py2viper_translation.lib.typedefs import (
    Function,
    Method,
    Predicate,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.translators.common import CommonTranslator
from py2viper_translation.translators.io_operation.definition import (
    IOOperationDefinitionTranslator,
)
from py2viper_translation.translators.io_operation.use import (
    IOOperationUseTranslator,
)


class IOOperationTranslator(CommonTranslator):
    """Class providing interface to translating IO operations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._use_translator = IOOperationUseTranslator(
            *args, **kwargs)
        self._definition_translator = IOOperationDefinitionTranslator(
            *args, **kwargs)

    def translate_io_operation(
            self, operation: PythonIOOperation,
            ctx: Context) -> Tuple[
                Predicate,
                List[Function],
                List[Method]]:
        return self._definition_translator.translate_io_operation(
            operation, ctx)

    def translate_io_operation_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        return self._use_translator.translate_io_operation_call(
            node, ctx)

    def is_io_existential_defining_equality(self, node: ast.expr,
                                            ctx: Context) -> bool:
        return self._use_translator.is_io_existential_defining_equality(
            node, ctx)

    def define_io_existential(self, node: ast.Compare, ctx: Context) -> None:
        self._use_translator.define_io_existential(
            node, ctx)

    def translate_get_ghost_output(self, node: ast.Assign,
                                   ctx: Context) -> List[Stmt]:
        return self._use_translator.translate_get_ghost_output(
            node, ctx)

    def translate_io_contractfunc_call(self, node: ast.Call,
                                       ctx: Context) -> StmtsAndExpr:
        return self._use_translator.translate_io_contractfunc_call(
            node, ctx)
