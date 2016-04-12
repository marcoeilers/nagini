import ast

from py2viper_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
)
from py2viper_translation.abstract_translator import (
    CommonTranslator,
    Context,
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.constants import BUILTINS
from py2viper_translation.containers import PythonClass, PythonMethod
from py2viper_translation.util import (
    get_all_fields,
    get_func_name,
    InvalidProgramException,
    is_two_arg_super_call
)
from typing import List


class CallTranslator(CommonTranslator):

    def translate_isinstance(self, node: ast.Call,
                             ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 2
        assert isinstance(node.args[1], ast.Name)
        stmt, obj = self.translate_expr(node.args[0], ctx)
        cls = ctx.program.classes[node.args[1].id]
        return stmt, self.type_factory.type_check(obj, cls, ctx)

    def translate_len(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        args = [target]
        call = self.get_function_call(node.args[0], '__len__', args, node, ctx)
        return stmt, call

    def translate_super(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if len(node.args) == 2:
            if is_two_arg_super_call(node, ctx):
                return self.translate_expr(node.args[1], ctx)
            else:
                raise InvalidProgramException(node, 'invalid.super.call')
        elif not node.args:
            arg_name = next(iter(ctx.current_function.args))
            return [], ctx.current_function.args[arg_name].ref
        else:
            raise InvalidProgramException(node, 'invalid.super.call')

    def var_concrete_type_check(self, name: str, type: PythonClass,
                                ctx: Context) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of exactly the given type.
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                      self.no_position(ctx),
                                      self.no_info(ctx))
        return self.type_factory.concrete_type_check(obj_var, type, ctx)

    def _translate_constructor_call(self, target_class: PythonClass,
            node: ast.Call, args: List, arg_stmts: List,
            ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the constructor of target_class with args, where
        node is the call node and arg_stmts are statements related to argument
        evaluation.
        """
        position = self.to_position(node, ctx)
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        fields = get_all_fields(target_class)
        new = self.viper.NewStmt(res_var.ref, fields, self.no_position(ctx),
                                 self.no_info(ctx))
        result_has_type = self.var_concrete_type_check(res_var.name, target_class,
                                                     ctx)
        # inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, self.no_position(ctx),
                                        self.no_info(ctx))
        args = [res_var.ref] + args
        stmts = [new, type_inhale]
        target = target_class.get_method('__init__')
        if target:
            target_class = target.cls
            targets = []
            if target.declared_exceptions:
                error_var = self.get_error_var(node, ctx)
                targets.append(error_var)
            method_name = target_class.get_method('__init__').sil_name
            init = self.viper.MethodCall(method_name,
                                         args, targets,
                                         self.to_position(node, ctx),
                                         self.no_info(ctx))
            stmts.append(init)
            if target.declared_exceptions:
                catchers = self.create_exception_catchers(error_var,
                    ctx.current_function.try_blocks, node, ctx)
                stmts = stmts + catchers
        return arg_stmts + stmts, res_var.ref

    def translate_set(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        if node.args:
            raise UnsupportedException(node)
        args = []
        res_var = ctx.current_function.create_variable('set',
            ctx.program.classes['set'], self.translator)
        targets = [res_var.ref]
        constr_call = self.viper.MethodCall('set___init__', args, targets,
                                            self.to_position(node, ctx),
                                            self.no_info(ctx))
        return [constr_call], res_var.ref

    def translate_builtin_func(self, node: ast.Call,
                               ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to a builtin function like len() or isinstance()
        """
        func_name = get_func_name(node)
        if func_name == 'isinstance':
            return self.translate_isinstance(node, ctx)
        elif func_name == 'super':
            return self.translate_super(node, ctx)
        elif func_name == 'len':
            return self.translate_len(node, ctx)
        elif func_name == 'set':
            return self.translate_set(node, ctx)
        else:
            raise UnsupportedException(node)

    def translate_method_call(self, target: PythonMethod, args: List[Expr],
                              arg_stmts: List[Stmt],
                              position: 'silver.ast.Position', node: ast.AST,
                              ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to an impure method.
        """
        targets = []
        result_var = None
        if ctx.current_function is None:
            if ctx.current_class is None:
                # global variable
                raise InvalidProgramException(node, 'purity.violated')
            else:
                # static field
                raise UnsupportedException(node)
        if target.type is not None:
            result_var = ctx.current_function.create_variable(
                target.name + '_res', target.type, self.translator)
            targets.append(result_var.ref)
        if target.declared_exceptions:
            error_var = self.get_error_var(node, ctx)
            targets.append(error_var)
        call = [self.viper.MethodCall(target.sil_name, args, targets,
                                      position,
                                      self.no_info(ctx))]
        if target.declared_exceptions:
            call = call + self.create_exception_catchers(error_var,
                ctx.current_function.try_blocks, node, ctx)
        return (arg_stmts + call,
                result_var.ref if result_var else None)

    def translate_normal_call(self, node: ast.Call,
                              ctx: Context) -> StmtsAndExpr:
        """
        Translates 'normal' function calls, i.e. function, method, constructor
        or predicate calls.
        """
        args = []
        formal_args = []
        arg_stmts = []
        for arg in node.args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_stmts = arg_stmts + arg_stmt
            args.append(arg_expr)
        name = get_func_name(node)
        position = self.to_position(node, ctx)
        if name in ctx.program.classes:
            # this is a constructor call
            target_class = ctx.program.classes[name]
            return self._translate_constructor_call(target_class, node, args,
                                                    arg_stmts, ctx)
        is_predicate = True
        if isinstance(node.func, ast.Attribute):
            # method called on an object
            rec_stmt, receiver = self.translate_expr(node.func.value, ctx)
            receiver_class = self.get_type(node.func.value, ctx)
            target = receiver_class.get_predicate(node.func.attr)
            if not target:
                target = receiver_class.get_func_or_method(node.func.attr)
                is_predicate = False
            receiver_class = target.cls
            arg_stmts = rec_stmt + arg_stmts
            args = [receiver] + args
        else:
            # global function/method called
            receiver_class = None
            target = ctx.program.predicates.get(name)
            if not target:
                target = ctx.program.get_func_or_method(name)
                is_predicate = False
        for arg in target.args:
            formal_args.append(target.args[arg].decl)
        target_name = target.sil_name
        if is_predicate:
            if receiver_class:
                family_root = receiver_class
                while (family_root.superclass and
                       family_root.superclass.get_predicate(name)):
                    family_root = family_root.superclass
                target_name = family_root.get_predicate(name).sil_name
            perm = self.viper.FullPerm(position, self.no_info(ctx))
            return arg_stmts, self.create_predicate_access(target_name, args,
                                                           perm, node, ctx)
        elif target.pure:
            type = self.translate_type(target.type, ctx)
            return (arg_stmts, self.viper.FuncApp(target_name, args,
                                                  position,
                                                  self.no_info(ctx),
                                                  type,
                                                  formal_args))
        else:
            return self.translate_method_call(target, args, arg_stmts,
                                              position, node, ctx)

    def translate_Call(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates any kind of call. This can be a call to a contract function
        like Assert, a builtin Python function like isinstance, a
        constructor call, a 'call' to a predicate, a pure function or impure
        method call, on a receiver object or not.
        """
        if get_func_name(node) in CONTRACT_WRAPPER_FUNCS:
            raise ValueError('Contract call translated as normal call.')
        elif get_func_name(node) in CONTRACT_FUNCS:
            return self.translate_contractfunc_call(node, ctx)
        elif get_func_name(node) in BUILTINS:
            return self.translate_builtin_func(node, ctx)
        else:
            return self.translate_normal_call(node, ctx)
