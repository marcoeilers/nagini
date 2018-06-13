"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.extended_ast.translators.contract import (
    ExtendedASTContractTranslator
)
from nagini_translation.extended_ast.translators.expression import (
    ExtendedASTExpressionTranslator
)
from nagini_translation.extended_ast.translators.method import (
    ExtendedASTMethodTranslator
)
from nagini_translation.extended_ast.translators.statement import (
    ExtendedASTStatementTranslator
)
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translator import Translator
from nagini_translation.translators.abstract import TranslatorConfig
from nagini_translation.translators.call import CallTranslator
from nagini_translation.translators.io_operation import IOOperationTranslator
from nagini_translation.translators.obligation import ObligationTranslator
from nagini_translation.translators.permission import PermTranslator
from nagini_translation.translators.predicate import PredicateTranslator
from nagini_translation.translators.program import ProgramTranslator
from nagini_translation.translators.pure import PureTranslator
from nagini_translation.translators.type import TypeTranslator
from nagini_translation.translators.type_domain_factory import \
    TypeDomainFactory


class ExtendedASTTranslator(Translator):
    """
    Translator producing extended Silver AST.
    """
    def __init__(self, jvm: JVM, source_file: str, type_info: TypeInfo,
                 viper_ast: ViperAST):
        config = TranslatorConfig(self)
        config.pure_translator = PureTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.call_translator = CallTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.contract_translator = ExtendedASTContractTranslator(config, jvm,
                                                                   source_file,
                                                                   type_info,
                                                                   viper_ast)
        config.expr_translator = ExtendedASTExpressionTranslator(config, jvm,
                                                      source_file,
                                                      type_info, viper_ast)
        config.pred_translator = PredicateTranslator(config, jvm, source_file,
                                                     type_info, viper_ast)
        config.io_operation_translator = IOOperationTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.obligation_translator = ObligationTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.stmt_translator = ExtendedASTStatementTranslator(config, jvm,
                                                                source_file,
                                                                type_info, viper_ast)
        config.perm_translator = PermTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.type_translator = TypeTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.prog_translator = ProgramTranslator(config, jvm, source_file,
                                                   type_info, viper_ast)
        config.method_translator = ExtendedASTMethodTranslator(config, jvm, source_file,
                                                    type_info, viper_ast)
        config.type_factory = TypeDomainFactory(viper_ast, self)

        self.obligation_translator = config.obligation_translator
        self.prog_translator = config.prog_translator
        self.expr_translator = config.expr_translator
