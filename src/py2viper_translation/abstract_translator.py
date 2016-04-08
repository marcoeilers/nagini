import ast
import copy

from py2viper_translation.analyzer import (
    PythonClass,
    PythonMethod,
    PythonTryBlock,
    PythonProgram,
    PythonVar
)
from py2viper_translation.jvmaccess import JVM
from py2viper_translation.typeinfo import TypeInfo
from py2viper_translation.util import UnsupportedException
from py2viper_translation.viper_ast import ViperAST
from typing import List, Tuple, Optional, Any


Expr = 'silver.ast.Exp'
Stmt = 'silver.ast.Stmt'
StmtAndExpr = Tuple[List[Stmt], Expr]

class Context:
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

    def __init__(self, translator):
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

class AbstractTranslator:

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

    def translate_function(self, func: PythonMethod, ctx) -> 'silver.ast.Function':
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

    def create_subtyping_check(self,
                               method: PythonMethod, ctx) -> 'silver.ast.Callable':
        return self.config.method_translator.create_subtyping_check(method, ctx)

class CommonTranslator(AbstractTranslator):

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

    def _get_function_call(self, receiver, func_name, args, node, ctx):
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

    def contains_stmt(self, container: Any, contained: ast.AST) -> bool:
        """
        Checks if 'contained' is a part of the partial AST
        whose root is 'container'.
        """
        if container is contained:
            return True
        if isinstance(container, list):
            for stmt in container:
                if self.contains_stmt(stmt, contained):
                    return True
            return False
        elif isinstance(container, ast.AST):
            for field in container._fields:
                if self.contains_stmt(getattr(container, field), contained):
                    return True
            return False
        else:
            return False

    def _get_surrounding_try_blocks(self, try_blocks: List[PythonTryBlock],
                                    stmt: ast.AST) -> List[PythonTryBlock]:
        """
        Finds the try blocks in try_blocks that protect the statement stmt.
        """
        def rank(b: PythonTryBlock, blocks: List[PythonTryBlock]) -> int:
            result = 0
            for b2 in blocks:
                if self.contains_stmt(b2.protected_region, b.node):
                    result += 1
            return -result
        tb = try_blocks
        blocks = [b for b in tb if self.contains_stmt(b.protected_region, stmt)]
        inner_to_outer = sorted(blocks,key=lambda b: rank(b, blocks))
        return inner_to_outer

    def _get_all_fields(self, cls: PythonClass, selfvar: 'silver.ast.LocalVar',
                        position: 'silver.ast.Position', ctx) \
            -> Tuple['silver.ast.Field', 'silver.ast.FieldAccessPredicate']:
        accs = []
        fields = []
        while cls is not None:
            for fieldname in cls.fields:
                field = cls.fields[fieldname]
                if field.inherited is None:
                    fields.append(field.field)
                    acc = self.viper.FieldAccess(selfvar, field.field,
                                                 position, self.noinfo(ctx))
                    perm = self.viper.FullPerm(position, self.noinfo(ctx))
                    pred = self.viper.FieldAccessPredicate(acc,
                                                           perm,
                                                           position,
                                                           self.noinfo(ctx))
                    accs.append(pred)
            cls = cls.superclass
        return fields, accs

    def _get_error_var(self, stmt: ast.AST, ctx) -> 'LocalVarRef':
        """
        Returns the error variable of the try-block protecting stmt, otherwise
        the error return variable of the surrounding function, otherwise
        creates a new local variable of type Exception.
        """
        tries = self._get_surrounding_try_blocks(ctx.current_function.try_blocks,
                                         stmt)
        if tries:
            return tries[0].get_error_var(self.translator).ref
        if ctx.current_function.declared_exceptions:
            return ctx.current_function.error_var
        else:
            new_var = ctx.current_function.create_variable('error',
                ctx.program.classes['Exception'], self.translator)
            return new_var.ref

    def _is_two_arg_super_call(self, node: ast.Call, ctx) -> bool:
        # two-arg super call: first arg must be a class, second a reference
        # to self
        return (isinstance(node.args[0], ast.Name) and
            (node.args[0].id in ctx.program.classes) and
            isinstance(node.args[1], ast.Name) and
            (node.args[1].id == next(iter(ctx.current_function.args))))

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