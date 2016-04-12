import ast

from abc import ABCMeta
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonMethod,
    PythonTryBlock,
    PythonVar
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_surrounding_try_blocks,
    UnsupportedException
)
from py2viper_translation.lib.viper_ast import ViperAST
from typing import List, Tuple


Expr = 'silver.ast.Exp'
Stmt = 'silver.ast.Stmt'
StmtsAndExpr = Tuple[List[Stmt], Expr]


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

    def translate_contractfunc_call(self, node: ast.Call,
                                    ctx: Context) -> StmtsAndExpr:
        return self.config.contract_translator.translate_contractfunc_call(node,
                                                                           ctx)


class CommonTranslator(AbstractTranslator, metaclass=ABCMeta):
    """
    Abstract class which all specialized translators extend. Provides some
    functionality which is needed by many or all specialized translators.
    """

    def translate_generic(self, node: ast.AST, ctx: Context) -> None:
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

    def to_position(self, node: ast.AST, ctx: Context) -> 'silver.ast.Position':
        """
        Extracts the position from a node.
        If ctx.position is set to override the actual position, returns that.
        """
        if ctx.position is not None:
            return ctx.position
        else:
            return self.viper.to_position(node)

    def no_position(self, ctx: Context) -> 'silver.ast.Position':
        return self.to_position(None, ctx)

    def to_info(self, comments: List[str], ctx: Context) -> 'silver.ast.Info':
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

    def no_info(self, ctx: Context) -> 'silver.ast.Info':
        return self.to_info([], ctx)

    def get_function_call(self, receiver: ast.AST, func_name: str,
                          args: List[Expr], node: ast.AST,
                          ctx: Context) -> 'silver.ast.FuncApp':
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments.
        """
        target_cls = self.get_type(receiver, ctx)
        func = target_cls.get_function(func_name)
        formal_args = []
        for arg in func.args.values():
            formal_args.append(arg.decl)
        type = self.translate_type(func.type, ctx)
        sil_name = func.sil_name
        call = self.viper.FuncApp(sil_name, args, self.to_position(node, ctx),
                                  self.no_info(ctx), type, formal_args)
        return call

    def get_error_var(self, stmt: ast.AST,
                      ctx: Context) -> 'silver.ast.LocalVarRef':
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

    def var_type_check(self, name: str, type: PythonClass,
                       ctx: Context) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of the given type.
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                      self.no_position(ctx),
                                      self.no_info(ctx))
        return self.type_factory.type_check(obj_var, type, ctx)

    def create_predicate_access(self, pred_name: str, args: List, perm: Expr,
                                 node: ast.AST, ctx: Context) -> Expr:
        """
        Creates a predicate access for the predicate with the given name,
        with the given args and permission.
        """
        pred_acc = self.viper.PredicateAccess(args, pred_name,
                                              self.to_position(node, ctx),
                                              self.no_info(ctx))
        pred_acc_pred = self.viper.PredicateAccessPredicate(pred_acc, perm,
            self.to_position(node, ctx), self.no_info(ctx))
        return pred_acc_pred
