import ast

from abc import ABCMeta
from py2viper_translation.lib.constants import PRIMITIVES
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonExceptionHandler,
    PythonMethod,
    PythonTryBlock,
    PythonType,
    PythonVar,
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_surrounding_try_blocks,
    InvalidProgramException,
    UnsupportedException
)
from py2viper_translation.lib.viper_ast import ViperAST
from typing import List, Tuple, Union


# TODO: Move these typedefs to separate file and add more of them.
Expr = 'silver.ast.Exp'
Stmt = 'silver.ast.Stmt'
StmtsAndExpr = Tuple[List[Stmt], Expr]
VarDecl = 'silver.ast.LocalVarDecl'
DomainFuncApp = 'silver.ast.DomainFuncApp'


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

    def get_function_call(self, receiver: Union[ast.AST, PythonType],
                          func_name: str, args: List[Expr], node: ast.AST,
                          ctx: Context) -> 'silver.ast.FuncApp':
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments.
        """
        if receiver:
            if isinstance(receiver, ast.AST):
                target_cls = self.get_type(receiver, ctx)
            else:
                target_cls = receiver
            func = target_cls.get_function(func_name)
        else:
            func = ctx.program.functions[func_name]
        if not func:
            raise InvalidProgramException(node, 'unknown.function.called')
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
        tries = get_surrounding_try_blocks(ctx.actual_function.try_blocks,
                                           stmt)
        if tries:
            err_var = tries[0].get_error_var(self.translator)
            if err_var.sil_name in ctx.var_aliases:
                err_var = ctx.var_aliases[err_var.sil_name]
            return err_var.ref
        if ctx.actual_function.declared_exceptions:
            return ctx.error_var
        else:
            new_var = ctx.current_function.create_variable('error',
                ctx.program.classes['Exception'], self.translator)
            return new_var.ref

    def var_type_check(self, name: str, type: PythonType, perms: bool,
                       ctx: Context) -> Expr:
        """
        Creates an expression checking if the var with the given name
        is of the given type.
        """
        if name in ctx.var_aliases:
            obj_var = ctx.var_aliases[name].ref
        else:
            obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        return self.type_check(obj_var, type, perms, ctx)

    # TODO: move to type translator, reference in abstract translator
    def type_check(self, lhs: Expr, type: PythonType, perms: bool,
                   ctx: Context) -> Expr:
        if type.name in PRIMITIVES:
            # do we need some boxed integer type?
            if perms:
                # access to field
                field = self.viper.Field(type.name + '_value___', self.config.type_translator.translate_type(type, ctx), self.no_position(ctx), self.no_info(ctx))
                field_acc = self.viper.FieldAccess(lhs, field, self.no_position(ctx), self.no_info(ctx))
                one = self.viper.IntLit(1, self.no_position(ctx), self.no_info(ctx))
                hundred = self.viper.IntLit(100, self.no_position(ctx), self.no_info(ctx))
                perm = self.viper.FractionalPerm(one, hundred, self.no_position(ctx), self.no_info(ctx))
                pred = self.viper.FieldAccessPredicate(field_acc, perm, self.no_position(ctx), self.no_info(ctx))
                return pred
            return self.viper.TrueLit(self.no_position(ctx), self.no_info(ctx))
        result = self.type_factory.type_check(lhs, type, ctx)
        if type.name == 'Tuple':
            # length
            length = self.viper.IntLit(len(type.type_args), self.no_position(ctx), self.no_info(ctx))
            len_call = self.get_function_call(type, '__len__', [lhs], None, ctx)
            eq = self.viper.EqCmp(len_call, length, self.no_position(ctx), self.no_info(ctx))
            result = self.viper.And(result, eq, self.no_position(ctx), self.no_info(ctx))
            # types of contents
            for index in range(len(type.type_args)):
                # typeof getitem lessorequal type
                item = type.type_args[index]
                index_lit = self.viper.IntLit(index, self.no_position(ctx), self.no_info(ctx))
                item_call = self.get_function_call(type, '__getitem__', [lhs, index_lit], None, ctx)
                type_check = self.type_check(item_call, item, perms, ctx)
                result = result = self.viper.And(result, type_check, self.no_position(ctx), self.no_info(ctx))
        return result

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

    def add_handlers_for_inlines(self, ctx: Context) -> List[Stmt]:
        stmts = []
        old_var_valiases = ctx.var_aliases
        old_lbl_aliases = ctx.label_aliases
        for (added_method, var_aliases, lbl_aliases) in ctx.added_handlers:
            ctx.var_aliases = var_aliases
            ctx.label_aliases = lbl_aliases
            ctx.inlined_calls.append(added_method)
            for block in added_method.try_blocks:
                for handler in block.handlers:
                    stmts += self.translate_handler(handler, ctx)
                if block.else_block:
                    stmts += self.translate_handler(block.else_block, ctx)
                if block.finally_block:
                    stmts += self.translate_finally(block, ctx)
            ctx.inlined_calls.remove(added_method)
        ctx.added_handlers = []
        ctx.var_aliases = old_var_valiases
        ctx.label_aliases = old_lbl_aliases
        return stmts
