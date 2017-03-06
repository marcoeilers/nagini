import ast

from abc import ABCMeta
from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    BOXED_PRIMITIVES,
    INT_TYPE,
    PRIMITIVE_BOOL_TYPE,
    PRIMITIVE_INT_TYPE,
    UNION_TYPE,
)
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules
from py2viper_translation.lib.program_nodes import (
    GenericType,
    PythonClass,
    PythonExceptionHandler,
    PythonField,
    PythonIOOperation,
    PythonMethod,
    PythonModule,
    PythonNode,
    PythonTryBlock,
    PythonType,
    PythonVar,
)
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.resolver import get_target as do_get_target
from py2viper_translation.lib.typedefs import (
    Expr,
    FuncApp,
    Position,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_func_name,
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

    def convert_to_type(self, e: Expr, target_type, ctx: Context,
                        node: ast.AST = None) -> Expr:
        """
        Converts expression ``e`` to the Viper type ``target_type`` if said
        type is Ref, Bool or Int.
        """
        result = e
        if target_type == self.viper.Ref:
            result = self.to_ref(e, ctx)
        elif target_type == self.viper.Bool:
            result = self.to_bool(e, ctx, node)
        elif target_type == self.viper.Int:
            result = self.to_int(e, ctx)
        return result

    def to_ref(self, e: Expr, ctx: Context) -> Expr:
        """
        Converts the given expression to an expression of the Silver type Ref
        if it isn't already, either by boxing a primitive or undoing a
        previous unboxing operation.
        """
        result = e
        if e.typ() == self.viper.Int:
            if (isinstance(e, self.viper.ast.FuncApp) and
                    e.funcname() == 'int___unbox__'):
                result = e.args().head()
            else:
                prim_int = ctx.module.global_module.classes[PRIMITIVE_INT_TYPE]
                result = self.get_function_call(prim_int, '__box__',
                                                [result], [None], None, ctx,
                                                position=e.pos())
        elif e.typ() == self.viper.Bool:
            if (isinstance(e, self.viper.ast.FuncApp) and
                    e.funcname() == 'bool___unbox__'):
                result = e.args().head()
            else:
                prim_bool = ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE]
                result = self.get_function_call(prim_bool, '__box__',
                                                [result], [None], None, ctx,
                                                position=e.pos())
        return result

    def to_bool(self, e: Expr, ctx: Context, node: ast.AST = None) -> Expr:
        """
        Converts the given expression to an expression of the Silver type Bool
        if it isn't already, either by calling __bool__ on an object and
        possibly unboxing the result, or by undoing a previous boxing operation.
        """
        if e.typ() == self.viper.Bool:
            return e
        if e.typ() != self.viper.Ref:
            e = self.to_ref(e, ctx)
        if (isinstance(e, self.viper.ast.FuncApp) and
                e.funcname() == '__prim__bool___box__'):
            return e.args().head()
        result = e
        call_bool = True
        if node:
            node_type = self.get_type(node, ctx)
            if node_type.name == 'bool':
                call_bool = False
            if call_bool:
                result = self.get_function_call(node_type, '__bool__',
                                                [result], [None], node, ctx,
                                                position=e.pos())
        if result.typ() != self.viper.Bool:
            bool_type = ctx.module.global_module.classes['bool']
            result = self.get_function_call(bool_type, '__unbox__',
                                            [result], [None], node, ctx,
                                            position=e.pos())
        return result

    def to_int(self, e: Expr, ctx: Context) -> Expr:
        """
        Converts the given expression to an expression of the Silver type Int
        if it isn't already, either by unboxing a reference or undoing a
        previous boxing operation.
        """
        if e.typ() == self.viper.Int:
            return e
        if e.typ() != self.viper.Ref:
            e = self.to_ref(e, ctx)
        if (isinstance(e, self.viper.ast.FuncApp) and
                    e.funcname() == '__prim__int___box__'):
            return e.args().head()
        result = e
        int_type = ctx.module.global_module.classes[INT_TYPE]
        result = self.get_function_call(int_type, '__unbox__',
                                        [result], [None], None, ctx,
                                        position=e.pos())
        return result

    def unwrap(self, e: Expr) -> Expr:
        if isinstance(e, self.viper.ast.FuncApp):
            if (e.funcname().endswith('__box__') or
                    e.funcname().endswith('__unbox__')):
                return e.args().head()
        return e

    def to_position(
            self, node: ast.AST, ctx: Context, error_string: str=None,
            rules: Rules=None) -> 'silver.ast.Position':
        """
        Extracts the position from a node, assigns an ID to the node and stores
        the node and the position in the context for it.
        """
        return self.viper.to_position(node, ctx.position, error_string, rules)

    def no_position(self, ctx: Context, error_string: str=None,
            rules: Rules=None) -> 'silver.ast.Position':
        return self.to_position(None, ctx, error_string, rules)

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

    def normalize_type(self, typ: PythonType, ctx: Context) -> PythonType:
        """
        Normalizes a type, i.e., returns the actual NoneType if it's None,
        otherwise just returns the type.
        """
        if typ is None:
            return ctx.module.global_module.classes['NoneType']
        return typ

    def get_tuple_type_arg(self, arg: Expr, arg_type: PythonType, node: ast.AST,
                           ctx: Context) -> Expr:
        """
        Creates an expression of type PyType that represents the type of 'arg',
        to be handed to the constructor function for tuples. This is different
        than what's used elsewhere. For, e.g., Optional[NoneType, A, C], this
        will return
        arg == null ? NoneType : issubtype(typeof(arg), A) ? A : C
        """
        position = self.no_position(ctx)
        info = self.no_info(ctx)
        if arg_type.name == UNION_TYPE:
            first_arg = self.normalize_type(arg_type.type_args[0], ctx)
            result = self.type_factory.translate_type_literal(first_arg,
                                                              position, ctx)
            for option in arg_type.type_args[1:]:
                option = self.normalize_type(option, ctx)
                check = self.type_check(arg, option, position, ctx, False)
                type_lit = self.type_factory.translate_type_literal(option,
                                                                    position,
                                                                    ctx)
                result = self.viper.CondExp(check, type_lit, result, position,
                                            info)
            return result
        arg_type = self.normalize_type(arg_type, ctx)
        type_lit = self.type_factory.translate_type_literal(arg_type,
                                                            position, ctx)
        return type_lit

    def get_function_call(self, receiver: PythonType,
                          func_name: str, args: List[Expr],
                          arg_types: List[PythonType], node: ast.AST,
                          ctx: Context,
                          position: Position = None) -> FuncApp:
        """
        Creates a function application of the function called func_name, with
        the given receiver and arguments. Boxes arguments if necessary, and
        unboxed the result if needed as well.
        """
        if receiver:
            target_cls = receiver
            func = target_cls.get_function(func_name)
        else:
            for container in ctx.module.get_included_modules():
                if func_name in container.functions:
                    func = container.functions[func_name]
                    break
        if not func:
            raise InvalidProgramException(node, 'unknown.function.called')
        formal_args = []
        actual_args = []
        assert len(args) == len(func.get_args())
        for arg, param, type in zip(args, func.get_args(), arg_types):
            formal_args.append(param.decl)
            if param.type.name == '__prim__bool':
                actual_arg = self.to_bool(arg, ctx)
            elif param.type.name == '__prim__int':
                actual_arg = self.to_int(arg, ctx)
            else:
                actual_arg = self.to_ref(arg, ctx)
            actual_args.append(actual_arg)
        type = self.translate_type(func.type, ctx)
        sil_name = func.sil_name

        actual_position = position if position else self.to_position(node, ctx)
        call = self.viper.FuncApp(sil_name, actual_args,
                                  actual_position,
                                  self.no_info(ctx), type, formal_args)
        return call

    def get_method_call(self, receiver: PythonType,
                        func_name: str, args: List[Expr],
                        arg_types: List[PythonType],
                        targets: List['silver.ast.LocalVarRef'],
                        node: ast.AST,
                        ctx: Context) -> List[Stmt]:
        """
        Creates a method call to the methoc called func_name, with
        the given receiver and arguments. Boxes arguments if necessary.
        """
        if receiver:
            target_cls = receiver
            func = target_cls.get_method(func_name)
        else:
            func = ctx.module.methods[func_name]
        if not func:
            raise InvalidProgramException(node, 'unknown.function.called')
        actual_args = []
        for arg, param, type in zip(args, func.get_args(), arg_types):
            if param.type.name == PRIMITIVE_BOOL_TYPE:
                actual_arg = self.to_bool(arg, ctx)
            elif param.type.name == '__prim__int':
                actual_arg = self.to_int(arg, ctx)
            else:
                actual_arg = self.to_ref(arg, ctx)
            actual_args.append(actual_arg)
        sil_name = func.sil_name
        call = self.create_method_call_node(
            ctx, sil_name, actual_args, targets, self.to_position(node, ctx),
            self.no_info(ctx), target_method=func, target_node=node)
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
                ctx.module.global_module.classes['Exception'], self.translator)
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

    def _get_string_value(self, string: str) -> int:
        """
        Computes an integer value that uniquely represents the given string.
        """
        result = 0
        for (index, char) in enumerate(string):
            result += pow(256, index) * ord(char)
        return result

    def is_valid_super_call(self, node: ast.Call, container) -> bool:
        """
        Checks if a super() call is valid:
        It must either have no arguments, or otherwise the
        first arg must be a class, the second a reference to self.
        """
        if not node.args:
            return True
        elif len(node.args) == 2:
            target = do_get_target(node.args[0],
                                   container.module.get_included_modules(),
                                   container)
            return (isinstance(target, PythonClass) and
                    isinstance(node.args[1], ast.Name) and
                    (node.args[1].id == next(iter(container.args))))
        else:
            return False

    def get_target(self, node: ast.AST, ctx: Context) -> PythonModule:
        container = ctx.actual_function if ctx.actual_function else ctx.module
        containers = [ctx]
        if isinstance(container, (PythonMethod, PythonIOOperation)):
            containers.append(container)
            containers.extend(container.module.get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        result = do_get_target(node, containers, container)
        return result

    def get_fresh_int_lit(self, ctx: Context) -> Expr:
        """
        Returns an integer literal with a fresh value.
        """
        return self.viper.IntLit(ctx.get_fresh_int(), self.no_position(ctx),
                                 self.no_info(ctx))
