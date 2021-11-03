"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.analyzer import PythonModule, PythonVar
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.program_nodes import (
    ContainerInterface,
    PythonMethod,
    PythonNode,
)
from nagini_translation.lib.resolver import get_target
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.abstract import (
    Context,
    Expr,
    TranslatorConfig,
)
from nagini_translation.translators.call import CallTranslator
from nagini_translation.translators.contract import ContractTranslator
from nagini_translation.translators.expression import ExpressionTranslator
from nagini_translation.translators.io_operation import (
    IOOperationTranslator,
)
from nagini_translation.translators.method import MethodTranslator
from nagini_translation.translators.obligation import (
    ObligationTranslator,
)
from nagini_translation.translators.permission import PermTranslator
from nagini_translation.translators.predicate import PredicateTranslator
from nagini_translation.translators.program import ProgramTranslator
from nagini_translation.translators.pure import PureTranslator
from nagini_translation.translators.statement import StatementTranslator
from nagini_translation.translators.type import TypeTranslator
from nagini_translation.translators.type_domain_factory import (
    TypeDomainFactory,
)
from typing import List, Optional, Set


class Translator:
    """
    Translates a Python AST to a Silver AST.
    This class serves as the public interface of the entire translator.
    The functionality is implemented in several specialized translators; this
    class only sets up the inner translator structure and forwards calls from
    the public interface to the responsible specialized translators.
    """

    def __init__(self, jvm: JVM, source_file: str, type_info: TypeInfo,
                 viper_ast: ViperAST):
        config = TranslatorConfig(self)
        config.pure_translator = PureTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.call_translator = CallTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.contract_translator = ContractTranslator(config, jvm,
                                                        source_file,
                                                        type_info, viper_ast)
        config.expr_translator = ExpressionTranslator(config, jvm, source_file,
                                                      type_info, viper_ast)
        config.pred_translator = PredicateTranslator(config, jvm, source_file,
                                                     type_info, viper_ast)
        config.io_operation_translator = IOOperationTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.obligation_translator = ObligationTranslator(
            config, jvm, source_file, type_info, viper_ast)
        config.stmt_translator = StatementTranslator(config, jvm, source_file,
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
                          ignore_global: bool = False,
                          arp: bool = False,
                          sif = False) -> 'silver.ast.Program':
        ctx = Context()
        ctx.sif = sif
        ctx.current_class = None
        ctx.current_function = None
        ctx.module = modules[0]
        ctx.arp = arp
        return self.prog_translator.translate_program(modules, sil_progs, ctx,
                                                      selected, ignore_global)

    def translate_pythonvar_decl(self, var: PythonVar,
            module: PythonModule) -> 'silver.ast.LocalVarDecl':
        # We need a context object here
        ctx = Context()
        ctx.module = module
        return self.expr_translator.translate_pythonvar_decl(var, ctx)

    def translate_pythonvar_ref(self, var: PythonVar,
                                module: PythonModule,
                                node: ast.AST, ctx: Context) -> Expr:
        # We need a context object here
        if not ctx:
            ctx = Context()
            ctx.module = module
        return self.expr_translator.translate_pythonvar_ref(var, node, ctx)

    def to_position(self, node: ast.AST, ctx: Context) -> 'silver.ast.Position':
        return self.expr_translator.to_position(node, ctx)

    def no_position(self, ctx: Context) -> 'silver.ast.Position':
        return self.to_position(None, ctx)

    def to_info(self, comments: List[str], ctx: Context) -> 'silver.ast.Info':
        return self.expr_translator.to_info(comments, ctx)

    def no_info(self, ctx: Context) -> 'silver.ast.Info':
        return self.to_info([], ctx)

    def set_required_names(self, name: str, required_names: Set[str]) -> None:
        """
        Registers that the native Silver method/function named 'name' depends
        on the methods/functions in the given set.
        """
        self.prog_translator.required_names[name] = required_names

    def create_obligation_info(self, method: PythonMethod) -> object:
        """
        Create an obligation info for method. This method should be
        called during the processing stage of the method before any
        translation is done.

        This return type of this method is ``object`` to indicate that
        the returned value is opaque for all code except obligation
        translator.
        """
        return self.obligation_translator.create_obligation_info(method)

    def get_target(self, node: ast.AST,
                   containers: List[ContainerInterface],
                   container: PythonNode) -> PythonNode:
        return get_target(node, containers, container)
