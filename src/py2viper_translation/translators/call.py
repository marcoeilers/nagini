import ast

from py2viper_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
)
from py2viper_translation.lib.constants import (
    BUILTINS,
    END_LABEL,
    ERROR_NAME,
    RESULT_NAME
)
from py2viper_translation.lib.program_nodes import (
    PythonClass,
    PythonMethod,
    PythonVar
)
from py2viper_translation.lib.util import (
    get_body_start_index,
    get_func_name,
    InvalidProgramException,
    is_two_arg_super_call,
    UnsupportedException,
)
from py2viper_translation.translators.abstract import (
    CommonTranslator,
    Context,
    Expr,
    Stmt,
    StmtsAndExpr,
)
from typing import List, Tuple


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
            arg_name = next(iter(ctx.actual_function.args))
            if ctx.var_aliases and arg_name in ctx.var_aliases:
                replacement = ctx.var_aliases[arg_name]
                if isinstance(replacement, PythonVar):
                    return replacement.ref
                else:
                    return replacement
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
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        fields = target_class.get_all_sil_fields()
        new = self.viper.NewStmt(res_var.ref, fields, self.no_position(ctx),
                                 self.no_info(ctx))
        result_has_type = self.var_concrete_type_check(res_var.name,
                                                       target_class,
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
                    ctx.actual_function.try_blocks, node, ctx)
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
                raise UnsupportedException(node, "Global function call "
                                           "not supported.")
            else:
                # static field
                raise UnsupportedException(node, "Static fields not supported.")
        if target.type is not None:
            result_var = result_var = ctx.current_function.create_variable(
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
                ctx.actual_function.try_blocks, node, ctx)
        return (arg_stmts + call,
                result_var.ref if result_var else None)

    def _translate_args(self, node: ast.Call,
                        ctx: Context) -> Tuple[List[Stmt], List[Expr]]:
        args = []
        arg_stmts = []
        for arg in node.args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_stmts += arg_stmt
            args.append(arg_expr)

        return arg_stmts, args

    def inline_method(self, method: PythonMethod, args: List[PythonVar], result_var: PythonVar, error_var: PythonVar, ctx: Context) -> List[Stmt]:
        old_label_aliases = ctx.label_aliases
        old_var_aliases = ctx.var_aliases
        var_aliases = {}

        for name, arg in zip(method.args.keys(), args):
            var_aliases[name] = arg

        var_aliases[RESULT_NAME] = result_var
        if error_var:
            var_aliases[ERROR_NAME] = error_var

        ctx.inlined_calls.append(method)
        ctx.var_aliases = var_aliases
        ctx.label_aliases = {}

        for local_name, local in method.locals.items():
            local_var = ctx.current_function.create_variable(local_name, local.type, self.translator)
            ctx.var_aliases[local_name] = local_var

        # create label aliases
        for label in method.labels:
            new_label = ctx.current_function.get_fresh_name(label)
            ctx.label_aliases[label] = new_label
        end_label_name = ctx.label_aliases[END_LABEL]
        end_label = self.viper.Label(end_label_name, self.no_position(ctx), self.no_info(ctx))
        # translate body
        index = get_body_start_index(method.node.body)
        stmts = []
        for stmt in method.node.body[index:]:
            stmts += self.translate_stmt(stmt, ctx)
        stmts.append(end_label)
        # check for exceptions
        ctx.inlined_calls.remove(method)
        ctx.var_aliases = old_var_aliases
        ctx.label_aliases = old_label_aliases
        return stmts

    def inline_call(self, method: PythonMethod, node: ast.Call, is_super: bool, ctx: Context) -> StmtsAndExpr:
        assert ctx.current_function
        if method in ctx.inlined_calls:
            raise InvalidProgramException(node, 'recursive.static.call')
        var_aliases = {}
        args = []
        stmts = []
        if is_super:
            args.append(next(iter(ctx.actual_function.args.values())))
        for arg_val, arg in zip(node.args, method.args.values()):
            arg_stmt, arg_val = self.translate_expr(arg_val, ctx)
            stmts += arg_stmt
            arg_var = ctx.current_function.create_variable('arg', arg.type, self.translator)
            assign = self.viper.LocalVarAssign(arg_var.ref, arg_val, self.to_position(node, ctx), self.no_info(ctx))
            stmts.append(assign)
            args.append(arg_var)

        # create target vars
        res_var = ctx.current_function.create_variable(RESULT_NAME, method.type, self.translator)
        optional_error_var = None
        error_var = self.get_error_var(node, ctx)
        if method.declared_exceptions:
            optional_error_var = error_var

        inline_stmts = self.inline_method(method, args, res_var, optional_error_var, ctx)
        stmts += inline_stmts
        if method.declared_exceptions:
            stmts += self.create_exception_catchers(error_var,
                                                    ctx.actual_function.try_blocks,
                                                    node, ctx)
        # return result
        return stmts, res_var.ref

    def translate_normal_call(self, node: ast.Call,
                              ctx: Context) -> StmtsAndExpr:
        """
        Translates 'normal' function calls, i.e. function, method, constructor
        or predicate calls.
        """
        formal_args = []
        arg_stmts, args = self._translate_args(node, ctx)
        name = get_func_name(node)
        position = self.to_position(node, ctx)
        if name in ctx.program.classes:
            # this is a constructor call
            target_class = ctx.program.classes[name]
            return self._translate_constructor_call(target_class, node, args,
                                                    arg_stmts, ctx)
        is_predicate = True
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in ctx.program.classes:
                    # statically bound call
                    target_class = ctx.program.classes[node.func.value.id]
                    target = target_class.get_func_or_method(node.func.attr)
                    return self.inline_call(target, node, False, ctx)
            if isinstance(node.func.value, ast.Call):
                if get_func_name(node.func.value) == 'super':
                    # super call
                    target_class = self.get_type(node.func.value, ctx)
                    target = target_class.get_func_or_method(node.func.attr)
                    return self.inline_call(target, node, True, ctx)
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
