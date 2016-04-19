import ast

from py2viper_translation.analyzer import PythonProgram, PythonVar
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.abstract import (
    Context,
    Expr,
    TranslatorConfig,
)
from py2viper_translation.translators.call import CallTranslator
from py2viper_translation.translators.contract import ContractTranslator
from py2viper_translation.translators.expression import ExpressionTranslator
from py2viper_translation.translators.method import MethodTranslator
from py2viper_translation.translators.permission import PermTranslator
from py2viper_translation.translators.predicate import PredicateTranslator
from py2viper_translation.translators.program import ProgramTranslator
from py2viper_translation.translators.pure import PureTranslator
from py2viper_translation.translators.statement import StatementTranslator
from py2viper_translation.translators.type import TypeTranslator
from py2viper_translation.translators.type_domain_factory import (
    TypeDomainFactory,
)
from typing import List

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
        self.prog_translator = config.prog_translator
        self.expr_translator = config.expr_translator

    def translate_program(self, program: PythonProgram,
                          sil_progs: List) -> 'silver.ast.Program':
        ctx = Context()
        ctx.current_class = None
        ctx.current_function = None
        ctx.program = program
        return self.prog_translator.translate_program(program, sil_progs, ctx)

    def translate_pythonvar_decl(self, var: PythonVar,
            program: PythonProgram) -> 'silver.ast.LocalVarDecl':
        # we need a context object here
        ctx = Context()
        ctx.program = program
        return self.expr_translator.translate_pythonvar_decl(var, ctx)

    def translate_pythonvar_ref(self, var: PythonVar,
                                program: PythonProgram) -> Expr:
        # we need a context object here
        ctx = Context()
        ctx.program = program
        return self.expr_translator.translate_pythonvar_ref(var, ctx)

    def to_position(self, node: ast.AST, ctx: Context) -> 'silver.ast.Position':
        return self.expr_translator.to_position(node, ctx)

    def no_position(self, ctx: Context) -> 'silver.ast.Position':
        return self.to_position(None, ctx)

    def to_info(self, comments: List[str], ctx: Context) -> 'silver.ast.Info':
        return self.expr_translator.to_info(comments, ctx)

    def no_info(self, ctx: Context) -> 'silver.ast.Info':
        return self.to_info([], ctx)
