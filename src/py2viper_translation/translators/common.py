import ast

from abc import ABCMeta
from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    INT_TYPE,
    OPERATOR_FUNCTIONS,
    PRIMITIVES,
    UNION_TYPE,
)
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules
from py2viper_translation.lib.program_nodes import (
    get_target as do_get_target,
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
from py2viper_translation.lib.typedefs import (
    Expr,
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

    def __init__(self, config: 'TranslatorConfig', jvm: JVM, source_file: str,
                 type_info: 'TypeInfo', viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self.primitive_operations = {
            ast.Add: self.viper.Add,
            ast.Sub: self.viper.Sub,
            ast.Mult: self.viper.Mul,
            ast.FloorDiv: self.viper.Div,
            ast.Mod: self.viper.Mod,
        }

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

    def normalize_type(self, typ: PythonType, ctx: Context) -> PythonType:
        """
        Normalizes a type, i.e., converts it to the wrapper type if it's
        a primitive, returns the actual NoneType if it's None, otherwise just
        returns the type.
        """
        if typ is None:
            return ctx.module.global_module.classes['NoneType']
        if typ.name in PRIMITIVES:
            return ctx.module.global_module.classes['__boxed_' + typ.name]
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
            result = self.type_factory.translate_type_literal(first_arg, node,
                                                              ctx)
            for option in arg_type.type_args[1:]:
                option = self.normalize_type(option, ctx)
                check = self.type_check(arg, option, position, ctx, False)
                type_lit = self.type_factory.translate_type_literal(option,
                                                                    node, ctx)
                result = self.viper.CondExp(check, type_lit, result, position,
                                            info)
            return result
        arg_type = self.normalize_type(arg_type, ctx)
        type_lit = self.type_factory.translate_type_literal(arg_type,
                                                            node, ctx)
        return type_lit

    def translate_operator(self, left: Expr, right: Expr, left_type: PythonType,
                           right_type: PythonType, node: ast.AST,
                           ctx: Context) -> StmtsAndExpr:
        """
        Translates the invocation of the binary operator of 'node' on the
        given two arguments, either to a primitive Silver operation or to a
        function or method call.
        """
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)
        stmt = []
        if self._is_primitive_operation(node, left_type, right_type):
            op = self._get_primitive_operation(node)
            result = op(left, right, position, info)
        else:
            func_name = OPERATOR_FUNCTIONS[type(node.op)]
            called_method = left_type.get_func_or_method(func_name)
            if called_method.pure:
                result = self.get_function_call(left_type, func_name,
                                                [left, right],
                                                [left_type, right_type],
                                                node, ctx)
            else:
                result_type = called_method.type
                res_var = ctx.actual_function.create_variable('op_res',
                                                              result_type,
                                                              self.translator)
                stmt += self.get_method_call(left_type, func_name,
                                             [left, right],
                                             [left_type, right_type],
                                             [res_var.ref(node, ctx)], node,
                                             ctx)
                result = res_var.ref(node, ctx)
        return stmt, result

    def _is_primitive_operation(self, node: ast.AST, left_type: PythonClass,
                                right_type: PythonClass) -> bool:
        """
        Decides if the binary operation from node, called with arguments of the
        given types, should be translated as a native Silver operation or
        as a call to a special function.
        """
        if left_type.name in {INT_TYPE, BOOL_TYPE}:
            if right_type.name not in {INT_TYPE, BOOL_TYPE}:
                raise InvalidProgramException(node, 'invalid.operation.type')
            else:
                return True
        return False

    def _get_primitive_operation(self, node: ast.BinOp):
        """
        Returns the constructor for the Silver node representing the given
        operation. If, for example, 'node' is an addition, this will return
        self.viper.Add.
        """
        return self.primitive_operations[type(node.op)]

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
            for container in ctx.module.get_included_modules():
                if func_name in container.functions:
                    func = container.functions[func_name]
                    break
        if not func:
            raise InvalidProgramException(node, 'unknown.function.called')
        formal_args = []
        actual_args = []
        for arg, param, type in zip(args, func.args.values(), arg_types):
            formal_args.append(param.decl)
            if (type and type.name in PRIMITIVES and
                    param.type.name not in PRIMITIVES):
                # Have to box
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
            # Have to unbox
            call = self.unbox_primitive(call, node_type, node, ctx)
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
        for arg, param, type in zip(args, func.args.values(), arg_types):
            if (type and type.name in PRIMITIVES and
                    param.type.name not in PRIMITIVES):
                # Have to box
                actual_arg = self.box_primitive(arg, type, None, ctx)
            else:
                actual_arg = arg
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
            ctx.module.global_module.classes['__boxed_' + type.name], name,
            args, arg_types, node, ctx)
        return call

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
                                   container.get_module().get_included_modules(),
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
            containers.extend(container.get_module().get_included_modules())
        else:
            # Assume module
            containers.extend(container.get_included_modules())
        return do_get_target(node, containers, container)
