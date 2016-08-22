"""Public interface to IO operation translator."""


import ast

from typing import List, Tuple

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonIOOperation,
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typedefs import (
    Function,
    Method,
    Predicate,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.abstract import TranslatorConfig
from py2viper_translation.translators.io_operation.definition import (
    IOOperationDefinitionTranslator,
)
from py2viper_translation.translators.io_operation.use import (
    IOOperationUseTranslator,
)


class IOOperationTranslator:
    """Class providing interface to translating IO operations."""

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        self._use_translator = IOOperationUseTranslator(
            config, jvm, source_file, type_info, viper_ast)
        self._definition_translator = IOOperationDefinitionTranslator(
            config, jvm, source_file, type_info, viper_ast)

    def translate_io_operation(
            self, operation: PythonIOOperation,
            ctx: Context) -> Tuple[
                Predicate,
                List[Function],
                List[Method]]:
        """Translate IO operation to Silver."""
        return self._definition_translator.translate_io_operation(
            operation, ctx)

    def translate_io_operation_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        """Translate a call to an IO operation."""
        return self._use_translator.translate_io_operation_call(
            node, ctx)

    def is_io_existential_defining_equality(self, node: ast.expr,
                                            ctx: Context) -> bool:
        """Check if ``node`` defines IO existential variable."""
        return self._use_translator.is_io_existential_defining_equality(
            node, ctx)

    def define_io_existential(self, node: ast.Compare, ctx: Context) -> None:
        """From defining equality defines IO existential variable."""
        self._use_translator.define_io_existential(
            node, ctx)

    def translate_get_ghost_output(self, node: ast.Assign,
                                   ctx: Context) -> List[Stmt]:
        """Translate ``GetGhostOutput``."""
        return self._use_translator.translate_get_ghost_output(
            node, ctx)

    def translate_io_contractfunc_call(self, node: ast.Call,
                                       ctx: Context) -> StmtsAndExpr:
        """Translate a call to a IO contract function."""
        return self._use_translator.translate_io_contractfunc_call(
            node, ctx)
