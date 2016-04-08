import ast

from py2viper_translation.analyzer import PythonProgram, PythonVar
from py2viper_translation.pure_translator import PureTranslator
from py2viper_translation.call_translator import CallTranslator
from py2viper_translation.abstract_translator import TranslatorConfig, Expr, Context
from py2viper_translation.contract_translator import ContractTranslator
from py2viper_translation.expression_translator import ExpressionTranslator
from py2viper_translation.predicate_translator import PredicateTranslator
from py2viper_translation.statement_translator import StatementTranslator
from py2viper_translation.perm_translator import PermTranslator
from py2viper_translation.type_translator import TypeTranslator
from py2viper_translation.type_domain_factory import TypeDomainFactory
from py2viper_translation.program_translator import ProgramTranslator
from py2viper_translation.jvmaccess import JVM
from py2viper_translation.typeinfo import TypeInfo
from py2viper_translation.viper_ast import ViperAST
from typing import List


class Translator:
    """
    Translates a Python AST to a Silver AST
    """

    def __init__(self, jvm: JVM, sourcefile: str, typeinfo: TypeInfo,
                 viperast: ViperAST):
        config = TranslatorConfig(self)
        config.pure_translator = PureTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.call_translator = CallTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.contract_translator = ContractTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.expr_translator = ExpressionTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.pred_translator = PredicateTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.stmt_translator = StatementTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.perm_translator = PermTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.type_translator = TypeTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.prog_translator = ProgramTranslator(config, jvm, sourcefile, typeinfo, viperast)
        config.type_factory = TypeDomainFactory(viperast, self)
        self.prog_translator = config.prog_translator
        self.expr_translator = config.expr_translator

    def translate_program(self, program: PythonProgram,
                          sil_progs: List) -> 'silver.ast.Program':
        return self.prog_translator.translate_program(program, sil_progs)


    def translate_pythonvar_decl(self,
                                 var: PythonVar, program: PythonProgram) -> 'silver.ast.LocalVarDecl':
        # we need a context object here
        ctx = Context()
        ctx.program = program
        return self.expr_translator.translate_pythonvar_decl(var, ctx)

    def translate_pythonvar_ref(self, var: PythonVar, program: PythonProgram) -> Expr:
        # we need a context object here
        ctx = Context()
        ctx.program = program
        return self.expr_translator.translate_pythonvar_ref(var, ctx)

    def to_position(self, node, ctx):
        return self.expr_translator.to_position(node, ctx)

    def noposition(self, ctx):
        return self.to_position(None, ctx)

    def to_info(self, comments, ctx):
        return self.expr_translator.to_info(comments, ctx)

    def noinfo(self, ctx):
        return self.to_info([], ctx)