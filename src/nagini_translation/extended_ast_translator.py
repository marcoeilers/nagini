"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.program_nodes import PythonModule
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import PythonVar
from nagini_translation.translators.abstract import TranslatorConfig
from nagini_translation.translators.call import CallTranslator
from nagini_translation.translators.contract import ContractTranslator
from nagini_translation.translators.expression import (
    ExpressionTranslator,
)
from nagini_translation.translators.method import MethodTranslator
from nagini_translation.translators.program import ProgramTranslator
from nagini_translation.translators.pure import PureTranslator
from nagini_translation.extended_ast.translators.statement import (
    ExtendedASTStatementTranslator,
)
from nagini_translation.translator import Translator
from nagini_translation.translators.abstract import Expr
from nagini_translation.translators.io_operation import (
    IOOperationTranslator,
)
from nagini_translation.translators.obligation import (
    ObligationTranslator,
)
from nagini_translation.translators.permission import PermTranslator
from nagini_translation.translators.predicate import PredicateTranslator

from nagini_translation.translators.type import TypeTranslator
from nagini_translation.translators.type_domain_factory import (
    TypeDomainFactory
)
from typing import List, Set


class ExtendedASTTranslator(Translator):
    def __init__(self, jvm: JVM, source_file: str, type_info: TypeInfo,
                 viper_ast: ViperAST):
        config = TranslatorConfig(self)
        config.pure_translator = PureTranslator(config, jvm, source_file,
                                                   type_info, viper_ast)
        config.call_translator = CallTranslator(config, jvm, source_file,
                                                   type_info, viper_ast)
        config.contract_translator = ContractTranslator(config, jvm,
                                                            source_file,
                                                            type_info,
                                                           viper_ast)
        config.expr_translator = ExpressionTranslator(config, jvm,
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
        config.method_translator = MethodTranslator(config, jvm, source_file,
                                                        type_info, viper_ast)
        config.type_factory = TypeDomainFactory(viper_ast, self)

        self.obligation_translator = config.obligation_translator
        self.prog_translator = config.prog_translator
        self.expr_translator = config.expr_translator

    def translate_program(self, modules: List[PythonModule], sil_progs: List,
                          selected: Set[str] = None,
                          ignore_global: bool = False) -> 'silver.ast.Program':
        ctx = Context()
        ctx.current_class = None
        ctx.current_function = None
        ctx.module = modules[0]
        return self.prog_translator.translate_program(modules, sil_progs, ctx,
                                                      selected, ignore_global)

    def translate_pythonvar_decl(self, var: PythonVar,
            module: PythonModule) -> 'silver.ast.LocalVarDecl':
        # We need a context object here
        ctx = Context()
        ctx.module = module
        return self.expr_translator.translate_pythonvar_decl(var, ctx)

    def translate_pythonvar_ref(self, var: PythonVar,
                                module: PythonModule, node: ast.AST,
                                ctx: 'Context') -> Expr:
        if not ctx:
            # We need a context object here
            ctx = Context()
            ctx.module = module
        return self.expr_translator.translate_pythonvar_ref(var, node, ctx)
