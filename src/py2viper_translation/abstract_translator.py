import ast
import copy

from abc import ABCMeta
from py2viper_translation.analyzer import (
    PythonClass,
    PythonMethod,
    PythonTryBlock,
    PythonVar
)
from py2viper_translation.jvmaccess import JVM
from py2viper_translation.typeinfo import TypeInfo
from py2viper_translation.util import (
    UnsupportedException,
    get_surrounding_try_blocks
)
from py2viper_translation.viper_ast import ViperAST
from typing import List, Tuple

Expr = 'silver.ast.Exp'
Stmt = 'silver.ast.Stmt'
StmtAndExpr = Tuple[List[Stmt], Expr]

class Context:
    """
    Contains the current state of the entire translation process.
    """

    def __init__(self) -> None:
        self.current_function = None
        self.current_class = None
        self.var_aliases = None
        self.position = None
        self.info = None
        self.program = None

    def _clone(self) -> 'Context':
        return copy.copy(self)

    def set_current_function(self, func: PythonMethod) -> 'Context':
        result = self._clone()
        result.current_function = func
        return result

    def set_current_function(self, func: PythonMethod) -> 'Context':
        result = self._clone()
        result.current_function = func
        return result

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

    def __init__(self, config: TranslatorConfig, jvm: JVM, sourcefile: str,
                 typeinfo: TypeInfo, viperast: ViperAST) -> None:
        self.config = config
        self.viper = viperast
        self.jvm = jvm

    def _get_type_factory(self):
        return self.config.type_factory

    type_factory = property(_get_type_factory)

    def _get_translator(self):
        return self.config.translator

    translator = property(_get_translator)

    def translate_expr(self, node: ast.AST, ctx) -> StmtAndExpr:
        return self.config.expr_translator.translate_expr(node, ctx)

    def translate_to_bool(self, node: ast.AST, ctx) -> StmtAndExpr:
        return self.config.expr_translator.translate_to_bool(node, ctx)

    def translate_stmt(self, node: ast.AST, ctx) -> List[Stmt]:
        return self.config.stmt_translator.translate_stmt(node, ctx)

    def translate_contract(self, node: ast.AST, ctx) -> Expr:
        return self.config.contract_translator.translate_contract(node, ctx)

    def translate_perm(self, node: ast.AST, ctx) -> Expr:
        return self.config.perm_translator.translate_perm(node, ctx)

    def translate_exprs(self, nodes: List[ast.AST],
                        function: PythonMethod, ctx) -> Expr:
        return self.config.pure_translator.translate_exprs(nodes, function, ctx)

    def get_type(self, node: ast.AST, ctx) -> PythonClass:
        return self.config.type_translator.get_type(node, ctx)

    def translate_type(self, cls: PythonClass, ctx) -> 'silver.ast.Type':
        return self.config.type_translator.translate_type(cls, ctx)

    def translate_Call(self, node: ast.Call, ctx) -> StmtAndExpr:
        return self.config.call_translator.translate_Call(node, ctx)

    def translate_predicate(self, pred: PythonMethod,
                            ctx) -> 'ast.silver.Predicate':
        return self.config.pred_translator.translate_predicate(pred, ctx)

    def translate_method(self, method: PythonMethod, ctx) -> 'silver.ast.Method':
        return self.config.method_translator.translate_method(method, ctx)

    def translate_function(self,
                           func: PythonMethod, ctx) -> 'silver.ast.Function':
        return self.config.method_translator.translate_function(func, ctx)

    def translate_predicate_family(self, root: PythonMethod,
            preds: List[PythonMethod], ctx) -> 'ast.silver.Predicate':
        return self.config.pred_translator.translate_predicate_family(root,
                                                                      preds,
                                                                      ctx)

    def create_exception_catchers(self, var: PythonVar,
                                  try_blocks: List[PythonTryBlock],
                                  call: ast.Call, ctx) -> List[Stmt]:
        return self.config.expr_translator.create_exception_catchers(var,
                                                                     try_blocks,
                                                                     call, ctx)

    def extract_contract(self, method: PythonMethod, errorvarname: str,
                         is_constructor: bool,
                         ctx) -> Tuple[List[Expr], List[Expr]]:
        return self.config.method_translator.extract_contract(method,
                                                              errorvarname,
                                                              is_constructor,
                                                              ctx)


class CommonTranslator(AbstractTranslator, metaclass=ABCMeta):
    """
    Abstract class which all specialized translators extend. Provides some
    functionality which is needed by many or all specialized translators.
    """

    def translate_generic(self, node: ast.AST, ctx) -> None:
        """
        Visitor that is used if no other visitor is implemented.
        Simply raises an exception.
        """
        raise UnsupportedException(node)

    def translate_block(self, stmtlist: List['silver.ast.Stmt'],
                        position: 'silver.ast.Position',
                        info: 'silver.ast.Info') -> Stmt:
        """
        Wraps a (Python) list of (Viper) statements into a Viper block
        """
        body = []
        for stmt in stmtlist:
            body.append(stmt)
        return self.viper.Seqn(body, position, info)

    def to_position(self, node, ctx):
        """
        Extracts the position from a node.
        If ctx.position is set to override the actual position, returns that.
        """
        if ctx.position is not None:
            return ctx.position
        else:
            return self.viper.to_position(node)

    def noposition(self, ctx):
        return self.to_position(None, ctx)

    def to_info(self, comments, ctx):
        """
        Wraps the given comments into an Info object.
        If ctx.info is set to override the given info, returns that.
        """
        if ctx.info is not None:
            return ctx.info
        if comments:
            return self.viper.SimpleInfo(comments)
        else:
            return self.viper.NoInfo

    def noinfo(self, ctx):
        return self.to_info([], ctx)

    def get_function_call(self, receiver, func_name, args, node, ctx):
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments.
        """
        target_cls = self.get_type(receiver, ctx)
        func = target_cls.get_function(func_name)
        formal_args = []
        for arg in func.args:
            formal_args.append(func.args[arg].decl)
        type = self.translate_type(func.type, ctx)
        sil_name = func.sil_name
        call = self.viper.FuncApp(sil_name, args, self.to_position(node, ctx),
                                  self.noinfo(ctx), type, formal_args)
        return call

    def get_error_var(self, stmt: ast.AST, ctx) -> 'LocalVarRef':
        """
        Returns the error variable of the try-block protecting stmt, otherwise
        the error return variable of the surrounding function, otherwise
        creates a new local variable of type Exception.
        """
        tries = get_surrounding_try_blocks(ctx.current_function.try_blocks,
                                           stmt)
        if tries:
            return tries[0].get_error_var(self.translator).ref
        if ctx.current_function.declared_exceptions:
            return ctx.current_function.error_var
        else:
            new_var = ctx.current_function.create_variable('error',
                ctx.program.classes['Exception'], self.translator)
            return new_var.ref

    def var_has_type(self, name: str,
                     type: PythonClass, ctx) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of the given type.
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                     self.noposition(ctx),
                                     self.noinfo(ctx))
        return self.type_factory.has_type(obj_var, type, ctx)