import ast

from abc import ABCMeta
from py2viper_translation.lib.constants import PRIMITIVES
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonExceptionHandler,
    PythonIOOperation,
    PythonMethod,
    PythonTryBlock,
    PythonType,
    PythonVar,
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typedefs import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException
)
from py2viper_translation.lib.viper_ast import ViperAST
from typing import List, Tuple, Union


class TranslatorConfig:
    """
    Contains the configuration of the translator, i.e. all the parts
    (specialized translates) it consists of.
    """

    def __init__(self, translator: 'Translator'):
        self.expr_translator = None
        self.stmt_translator = None
        self.call_translator = None
        self.contract_translator = None
        self.perm_translator = None
        self.pure_translator = None
        self.type_translator = None
        self.pred_translator = None
        self.io_operation_translator = None
        self.prog_translator = None
        self.method_translator = None
        self.type_factory = None
        self.translator = translator


class AbstractTranslator(metaclass=ABCMeta):
    """
    Abstract class which all specialized translators extend. Provides a number
    of interface methods through which spcialized translators can interact, and
    forwards calls to those methods to the respective translators.
    """

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        self.config = config
        self.viper = viper_ast
        self.jvm = jvm

    @property
    def type_factory(self):
        return self.config.type_factory

    @property
    def translator(self):
        return self.config.translator

    def translate_expr(self, node: ast.AST, ctx: Context) -> StmtsAndExpr:
        return self.config.expr_translator.translate_expr(node, ctx)

    def translate_to_bool(self, node: ast.AST, ctx: Context) -> StmtsAndExpr:
        return self.config.expr_translator.translate_to_bool(node, ctx)

    def translate_stmt(self, node: ast.AST, ctx: Context) -> List[Stmt]:
        return self.config.stmt_translator.translate_stmt(node, ctx)

    def translate_contract(self, node: ast.AST, ctx: Context) -> Expr:
        return self.config.contract_translator.translate_contract(node, ctx)

    def translate_perm(self, node: ast.AST, ctx: Context) -> Expr:
        return self.config.perm_translator.translate_perm(node, ctx)

    def translate_exprs(self, nodes: List[ast.AST],
                        function: PythonMethod, ctx: Context) -> Expr:
        return self.config.pure_translator.translate_exprs(nodes, function, ctx)

    def get_type(self, node: ast.AST, ctx: Context) -> PythonClass:
        return self.config.type_translator.get_type(node, ctx)

    def translate_type(self, cls: PythonClass,
                       ctx: Context) -> 'silver.ast.Type':
        return self.config.type_translator.translate_type(cls, ctx)

    def translate_Call(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        return self.config.call_translator.translate_Call(node, ctx)

    def translate_predicate(self, pred: PythonMethod,
                            ctx: Context) -> 'ast.silver.Predicate':
        return self.config.pred_translator.translate_predicate(pred, ctx)

    def translate_io_operation(
            self,
            operation: PythonIOOperation,
            ctx: Context,
            ) -> Tuple[
                'ast.silver.Predicate',
                List['ast.silver.Function'],
                List['ast.silver.Method'],
                ]:
        return self.config.io_operation_translator.translate_io_operation(
            operation,
            ctx)

    def translate_method(self, method: PythonMethod,
                         ctx: Context) -> 'silver.ast.Method':
        return self.config.method_translator.translate_method(method, ctx)

    def translate_function(self, func: PythonMethod,
                           ctx: Context) -> 'silver.ast.Function':
        return self.config.method_translator.translate_function(func, ctx)

    def translate_predicate_family(self, root: PythonMethod,
            preds: List[PythonMethod], ctx: Context) -> 'ast.silver.Predicate':
        return self.config.pred_translator.translate_predicate_family(root,
                                                                      preds,
                                                                      ctx)

    def create_exception_catchers(self, var: PythonVar,
                                  try_blocks: List[PythonTryBlock],
                                  call: ast.Call, ctx: Context) -> List[Stmt]:
        return self.config.expr_translator.create_exception_catchers(var,
                                                                     try_blocks,
                                                                     call, ctx)

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         is_constructor: bool,
                         ctx: Context) -> Tuple[List[Expr], List[Expr]]:
        return self.config.method_translator.extract_contract(method,
                                                              errorvarname,
                                                              is_constructor,
                                                              ctx)

    def inline_method(self, method: PythonMethod, args: List[PythonVar],
                      result_var: PythonVar, error_var: PythonVar,
                      ctx: Context) -> List[Stmt]:
        return self.config.call_translator.inline_method(method, args,
                                                         result_var, error_var,
                                                         ctx)

    def translate_contractfunc_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        return self.config.contract_translator.translate_contractfunc_call(node,
                                                                           ctx)

    def translate_handler(self, handler: PythonExceptionHandler,
                          ctx: Context) -> List[Stmt]:
        return self.config.method_translator.translate_handler(handler, ctx)

    def translate_finally(self, block: PythonTryBlock,
                          ctx: Context) -> List[Stmt]:
        return self.config.method_translator.translate_finally(block, ctx)

    def type_check(self, lhs: Expr, type: PythonType, ctx: Context,
                   perms: bool=False) -> Expr:
        return self.config.type_translator.type_check(lhs, type, ctx,
                                                      perms=perms)

