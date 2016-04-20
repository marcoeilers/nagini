from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.program_nodes import PythonProgram
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import SIFPythonVar
from py2viper_translation.sif.translators.contract import SIFContractTranslator
from py2viper_translation.sif.translators.expression import (
    SIFExpressionTranslator,
)
from py2viper_translation.sif.translators.method import SIFMethodTranslator
from py2viper_translation.sif.translators.statement import (
    SIFStatementTranslator,
)
from py2viper_translation.translator import Translator
from py2viper_translation.translators.abstract import Expr, TranslatorConfig
from py2viper_translation.translators.call import CallTranslator
from py2viper_translation.translators.permission import PermTranslator
from py2viper_translation.translators.predicate import PredicateTranslator
from py2viper_translation.translators.program import ProgramTranslator
from py2viper_translation.translators.pure import PureTranslator

from py2viper_translation.translators.type import TypeTranslator
from py2viper_translation.translators.type_domain_factory import (
    TypeDomainFactory
)
from typing import List


class SIFTranslator(Translator):
    def __init__(self, jvm: JVM, source_file: str, type_info: TypeInfo,
                 viper_ast: ViperAST):
        config = TranslatorConfig(self)
        config.pure_translator = PureTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.call_translator = CallTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.contract_translator = SIFContractTranslator(config, jvm,
                                                            source_file,
                                                            type_info,
                                                           viper_ast)
        config.expr_translator = SIFExpressionTranslator(config, jvm,
                                                         source_file,
                                                         type_info, viper_ast)
        config.pred_translator = PredicateTranslator(config, jvm, source_file,
                                                     type_info, viper_ast)
        config.stmt_translator = SIFStatementTranslator(config, jvm,
                                                        source_file,
                                                        type_info, viper_ast)
        config.perm_translator = PermTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.type_translator = TypeTranslator(config, jvm, source_file,
                                                type_info, viper_ast)
        config.prog_translator = ProgramTranslator(config, jvm, source_file,
                                                   type_info, viper_ast)
        config.method_translator = SIFMethodTranslator(config, jvm, source_file,
                                                        type_info, viper_ast)
        config.type_factory = TypeDomainFactory(viper_ast, self)
        self.prog_translator = config.prog_translator
        self.expr_translator = config.expr_translator

    def translate_program(self, program: PythonProgram,
                          sil_progs: List) -> 'silver.ast.Program':
        ctx = SIFContext()
        ctx.current_class = None
        ctx.current_function = None
        ctx.program = program
        return self.prog_translator.translate_program(program, sil_progs, ctx)

    def translate_pythonvar_decl(self, var: SIFPythonVar,
            program: PythonProgram) -> 'silver.ast.LocalVarDecl':
        # we need a context object here
        ctx = SIFContext()
        ctx.program = program
        return self.expr_translator.translate_pythonvar_decl(var, ctx)

    def translate_pythonvar_ref(self, var: SIFPythonVar,
                                program: PythonProgram) -> Expr:
        # we need a context object here
        ctx = SIFContext()
        ctx.program = program
        return self.expr_translator.translate_pythonvar_ref(var, ctx)