"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from nagini_translation.sif.translators.call import (
    SIFCallTranslator
)
from nagini_translation.sif.translators.contract import (
    SIFContractTranslator
)
from nagini_translation.sif.translators.expression import (
    SIFExpressionTranslator
)
from nagini_translation.sif.translators.method import (
    SIFMethodTranslator
)
from nagini_translation.sif.translators.program import (
    SIFProgramTranslator
)
from nagini_translation.sif.translators.statement import (
    SIFStatementTranslator
)

from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translator import Translator
from nagini_translation.translators.abstract import TranslatorConfig
from nagini_translation.translators.io_operation import IOOperationTranslator
from nagini_translation.translators.obligation import ObligationTranslator
from nagini_translation.translators.permission import PermTranslator
from nagini_translation.translators.predicate import PredicateTranslator
from nagini_translation.translators.pure import PureTranslator
from nagini_translation.translators.type import TypeTranslator
from nagini_translation.translators.type_domain_factory import (
    TypeDomainFactory
)


class SIFTranslator(Translator):
    """
    Translator producing extended Silver AST.
    """
    def __init__(self, jvm: JVM, source_file: str, type_info: TypeInfo,
                 viper_ast: ViperAST):
        config = TranslatorConfig(self)
        config.pure_translator = PureTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.call_translator = SIFCallTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.contract_translator = SIFContractTranslator(config, jvm,
                                                           source_file,
                                                           type_info,
                                                           viper_ast)
        config.expr_translator = SIFExpressionTranslator(config, jvm,
                                                         source_file,
                                                         type_info, viper_ast)
        config.pred_translator = PredicateTranslator(config, jvm, source_file,
                                                     type_info, viper_ast)
        config.io_operation_translator = IOOperationTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.obligation_translator = ObligationTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.stmt_translator = SIFStatementTranslator(config, jvm,
                                                        source_file,
                                                        type_info, viper_ast)
        config.perm_translator = PermTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.type_translator = TypeTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.prog_translator = SIFProgramTranslator(config, jvm, source_file,
                                                      type_info, viper_ast)
        config.method_translator = SIFMethodTranslator(config, jvm, source_file,
                                                       type_info, viper_ast)
        config.type_factory = TypeDomainFactory(viper_ast, self)

        self.obligation_translator = config.obligation_translator
        self.prog_translator = config.prog_translator
        self.expr_translator = config.expr_translator
