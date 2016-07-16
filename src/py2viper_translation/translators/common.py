import ast

from abc import ABCMeta
from py2viper_translation.lib.constants import PRIMITIVES
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonExceptionHandler,
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
from py2viper_translation.translators.abstract import (
    AbstractTranslator,
    Context,
)
from typing import List, Tuple, Union


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

    def to_position(
            self, node: ast.AST, ctx: Context, error_string: str=None,
            rules: Rules=None) -> 'silver.ast.Position':
        """
        Extracts the position from a node, assigns an ID to the node and stores
        the node and the position in the context for it.
        """
        return self.viper.to_position(node, ctx.position, error_string, rules)

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

    def get_function_call(self, receiver: PythonType,
                          func_name: str, args: List[Expr],
                          arg_types: List[PythonType], node: ast.AST,
                          ctx: Context) -> 'silver.ast.FuncApp':
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments. Boxes arguments if necessary, and
        unboxed the result if needed as well.
        """
        if receiver:
            target_cls = receiver
            func = target_cls.get_function(func_name)
        else:
            func = ctx.program.functions[func_name]
        if not func:
            raise InvalidProgramException(node, 'unknown.function.called')
        formal_args = []
        actual_args = []
        for arg, param, type in zip(args, func.args.values(), arg_types):
            formal_args.append(param.decl)
            if (type and type.name in PRIMITIVES and
                    param.type.name not in PRIMITIVES):
                # have to box
                actual_arg = self.box_primitive(arg, type, None, ctx)
            else:
                actual_arg = arg
            actual_args.append(actual_arg)
        type = self.translate_type(func.type, ctx)
        sil_name = func.sil_name

        call = self.viper.FuncApp(sil_name, actual_args,
                                  self.to_position(node, ctx),
                                  self.no_info(ctx), type, formal_args)
        if node and not isinstance(node, ast.Assign):
            node_type = self.get_type(node, ctx)
        else:
            node_type = None
        if (node_type and node_type in PRIMITIVES and
                func.type.name not in PRIMITIVES):
            # have to unbox
            call = self.unbox_primitive(call, node_type, node, ctx)
        return call

    def get_method_call(self, receiver: PythonType,
                        func_name: str, args: List[Expr],
                        arg_types: List[PythonType],
                        targets: List['silver.ast.LocalVarRef'],
                        node: ast.AST,
                        ctx: Context) -> 'silver.ast.MethodCall':
        """
        Creates a method call to the methoc called func_name, with
        the given receiver and arguments. Boxes arguments if necessary.
        """
        if receiver:
            target_cls = receiver
            func = target_cls.get_method(func_name)
        else:
            func = ctx.program.methods[func_name]
        if not func:
            raise InvalidProgramException(node, 'unknown.function.called')
        actual_args = []
        for arg, param, type in zip(args, func.args.values(), arg_types):
            if (type and type.name in PRIMITIVES and
                    param.type.name not in PRIMITIVES):
                # have to box
                actual_arg = self.box_primitive(arg, type, None, ctx)
            else:
                actual_arg = arg
            actual_args.append(actual_arg)
        sil_name = func.sil_name
        call = self.viper.MethodCall(sil_name, actual_args, targets,
                                     self.to_position(node, ctx),
                                     self.no_info(ctx))
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
            return err_var.ref()
        if ctx.actual_function.declared_exceptions:
            return ctx.error_var.ref()
        else:
            new_var = ctx.current_function.create_variable('error',
                ctx.program.classes['Exception'], self.translator)
            return new_var.ref()

    def var_type_check(self, name: str, type: PythonType,
                       position: 'silver.ast.Position',
                       ctx: Context, inhale_exhale: bool=True) -> Expr:
        """
        Creates an expression checking if the var with the given name
        is of the given type.
        """
        if name in ctx.var_aliases:
            obj_var = ctx.var_aliases[name].ref()
        else:
            obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                          self.no_position(ctx),
                                          self.no_info(ctx))
        return self.type_check(obj_var, type, position, ctx,
                               inhale_exhale=inhale_exhale)

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

    def box_primitive(self, primitive: Expr, type: PythonType, node: ast.AST,
                      ctx: Context) -> StmtsAndExpr:
        """
        Wraps the primitive of type type into a Ref object.
        """
        args = [primitive]
        arg_types = [None]
        name = '__box__'
        call = self.get_function_call(type, name, args, arg_types, node, ctx)
        return call

    def unbox_primitive(self, box: Expr, type: PythonType, node: ast.AST,
                        ctx: Context) -> Expr:
        """
        Assuming box is a wrapper-Ref containing a primitive of type type,
        returns the boxed primitive.
        """
        args = [box]
        arg_types = [None]
        name = '__unbox__'
        call = self.get_function_call(
            ctx.program.classes['__boxed_' + type.name], name, args,
            arg_types, node, ctx)
        return call

    def _get_string_value(self, string: str) -> int:
        """
        Computes an integer value that uniquely represents the given string.
        """
        result = 0
        for (index, char) in enumerate(string):
            result += pow(256, index) * ord(char)
        return result
