import ast

from py2viper_translation.constants import BUILTINS
from py2viper_contracts.contracts import (
    CONTRACT_FUNCS,
    CONTRACT_WRAPPER_FUNCS
    )
from py2viper_translation.abstract_translator import (
    CommonTranslator,
    TranslatorConfig,
    Expr,
    StmtAndExpr
)
from py2viper_translation.analyzer import PythonClass, PythonMethod, PythonVar
from py2viper_translation.util import InvalidProgramException, get_func_name
from typing import List, Tuple, Optional, Union, Dict

class CallTranslator(CommonTranslator):

    def translate_result(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 0
        type = ctx.current_function.type
        if not ctx.current_function.pure:
            return (
                [], self.viper.LocalVar('_res', self.translate_type(type, ctx),
                                        self.noposition(ctx),
                                        self.noinfo(ctx)))
        else:
            return ([], self.viper.Result(self.translate_type(type, ctx),
                                          self.to_position(node, ctx),
                                          self.noinfo(ctx)))

    def translate_acc_predicate(self, node: ast.Call, perm: Expr, ctx) -> StmtAndExpr:
        call = node.args[0]
        args = []
        arg_stmts = []
        for arg in call.args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_stmts = arg_stmts + arg_stmt
            args.append(arg_expr)
        if isinstance(call.func, ast.Name):
            pred = ctx.program.get_predicate(call.func.id)
        elif isinstance(call.func, ast.Attribute):
            rec_stmt, receiver = self.translate_expr(call.func.value, ctx)
            assert not rec_stmt
            receiver_class = self.get_type(call.func.value, ctx)
            name = call.func.attr
            pred = receiver_class.get_predicate(name)
            args = [receiver] + args
        else:
            raise UnsupportedException(node)
        pred_name = pred.sil_name
        if pred.cls:
            family_root = pred.cls
            while (family_root.superclass and
                   family_root.superclass.get_predicate(name)):
                family_root = family_root.superclass
            pred_name = family_root.get_predicate(name).sil_name
        return [], self._create_predicate_access(pred_name, args, perm,
                                                 node, ctx)

    def translate_acc(self, node: ast.Call, ctx) -> StmtAndExpr:
        if len(node.args) == 1:
            perm = self.viper.FullPerm(self.to_position(node, ctx),
                                       self.noinfo(ctx))
        elif len(node.args) == 2:
            perm = self.translate_perm(node.args[1], ctx)
        else:
            raise UnsupportedException(node)
        if isinstance(node.args[0], ast.Call):
            # this is a predicate.
            return self.translate_acc_predicate(node, perm, ctx)
        stmt, fieldacc = self.translate_expr(node.args[0], ctx)
        if stmt:
            raise InvalidProgramException(node, 'purity.violated')
        pred = self.viper.FieldAccessPredicate(fieldacc, perm,
                                               self.to_position(node, ctx),
                                               self.noinfo(ctx))
        return [], pred

    def translate_implies(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 2
        cond_stmt, cond = self.translate_expr(node.args[0], ctx)
        then_stmt, then = self.translate_expr(node.args[1], ctx)
        implication = self.viper.Implies(cond, then,
                                         self.to_position(node, ctx),
                                         self.noinfo(ctx))
        return (cond_stmt + then_stmt, implication)

    def translate_old(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 1
        stmt, exp = self.translate_expr(node.args[0], ctx)
        res = self.viper.Old(exp, self.to_position(node, ctx), self.noinfo(ctx))
        return (stmt, res)

    def translate_fold(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 1
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        assert not pred_stmt
        fold = self.viper.Fold(pred, self.to_position(node, ctx), self.noinfo(ctx))
        return [fold], None

    def translate_unfold(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 1
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        assert not pred_stmt
        unfold = self.viper.Unfold(pred, self.to_position(node, ctx), self.noinfo(ctx))
        return [unfold], None

    def translate_unfolding(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 2
        pred_stmt, pred = self.translate_expr(node.args[0], ctx)
        assert not pred_stmt
        expr_stmt, expr = self.translate_expr(node.args[1], ctx)
        unfold = self.viper.Unfolding(pred, expr, self.to_position(node, ctx),
                                      self.noinfo(ctx))
        return expr_stmt, unfold

    def translate_contractfunc_call(self, node: ast.Call, ctx) -> StmtAndExpr:
        """
        Translates calls to contract functions like Result() and Acc()
        """
        if get_func_name(node) == 'Result':
            return self.translate_result(node, ctx)
        elif get_func_name(node) == 'Acc':
            return self.translate_acc(node, ctx)
        elif get_func_name(node) == 'Implies':
            return self.translate_implies(node, ctx)
        elif get_func_name(node) == 'Old':
            return self.translate_old(node, ctx)
        elif get_func_name(node) == 'Fold':
            return self.translate_fold(node, ctx)
        elif get_func_name(node) == 'Unfold':
            return self.translate_unfold(node, ctx)
        elif get_func_name(node) == 'Unfolding':
            return self.translate_unfolding(node, ctx)
        else:
            raise UnsupportedException(node)

    def translate_isinstance(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 2
        assert isinstance(node.args[1], ast.Name)
        stmt, obj = self.translate_expr(node.args[0], ctx)
        cls = ctx.program.classes[node.args[1].id]
        return stmt, self.type_factory.has_type(obj, cls, ctx)

    def translate_len(self, node: ast.Call, ctx) -> StmtAndExpr:
        assert len(node.args) == 1
        stmt, target = self.translate_expr(node.args[0], ctx)
        args = [target]
        call = self._get_function_call(node.args[0], '__len__', args, node, ctx)
        return stmt, call

    def translate_super(self, node: ast.Call, ctx) -> StmtAndExpr:
        if len(node.args) == 2:
            if self._is_two_arg_super_call(node, ctx):
                return self.translate_expr(node.args[1], ctx)
            else:
                raise InvalidProgramException(node, 'invalid.super.call')
        elif not node.args:
            arg_name = next(iter(ctx.current_function.args))
            return [], ctx.current_function.args[arg_name].ref
        else:
            raise InvalidProgramException(node, 'invalid.super.call')

    def _create_predicate_access(self, pred_name: str, args: List, perm: Expr,
                                 node: ast.AST, ctx) -> Expr:
        pred_acc = self.viper.PredicateAccess(args, pred_name,
                                              self.to_position(node, ctx),
                                              self.noinfo(ctx))
        pred_acc_pred = self.viper.PredicateAccessPredicate(pred_acc, perm,
            self.to_position(node, ctx), self.noinfo(ctx))
        return pred_acc_pred

    def var_has_concrete_type(self, name: str,
                              type: PythonClass, ctx) -> 'silver.ast.DomainFuncApp':
        """
        Creates an expression checking if the var with the given name
        is of exactly the given type.
        """
        obj_var = self.viper.LocalVar(name, self.viper.Ref,
                                     self.noposition(ctx),
                                     self.noinfo(ctx))
        return self.type_factory.has_concrete_type(obj_var, type, ctx)

    def _translate_constructor_call(self, target_class: PythonClass,
            node: ast.Call, args: List, arg_stmts: List, ctx) -> StmtAndExpr:
        """
        Translates a call to the constructor of target_class with args, where
        node is the call node and arg_stmts are statements related to argument
        evaluation.
        """
        position = self.to_position(node, ctx)
        res_var = ctx.current_function.create_variable(target_class.name +'_res',
                                                        target_class,
                                                        self.translator)
        fields, _ = self._get_all_fields(target_class, res_var.ref, position, ctx)
        new = self.viper.NewStmt(res_var.ref, fields, self.noposition(ctx),
                                 self.noinfo(ctx))
        result_has_type = self.var_has_concrete_type(res_var.name, target_class, ctx)
        # inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, self.noposition(ctx),
                                        self.noinfo(ctx))
        args = [res_var.ref] + args
        stmts = [new, type_inhale]
        target = target_class.get_method('__init__')
        if target:
            target_class = target.cls
            targets = []
            if target.declared_exceptions:
                error_var = self._get_error_var(node)
                targets.append(error_var)
            method_name = target_class.get_method('__init__').sil_name
            init = self.viper.MethodCall(method_name,
                                         args, targets,
                                         self.to_position(node, ctx),
                                         self.noinfo(ctx))
            stmts.append(init)
            if target.declared_exceptions:
                catchers = self.create_exception_catchers(error_var,
                    ctx.current_function.try_blocks, node, ctx)
                stmts = stmts + catchers
        return arg_stmts + stmts, res_var.ref

    def translate_set(self, node: ast.Call, ctx) -> StmtAndExpr:
        if node.args:
            raise UnsupportedException(node)
        args = []
        res_var = ctx.current_function.create_variable('set',
            ctx.program.classes['set'], self.translator)
        targets = [res_var.ref]
        constr_call = self.viper.MethodCall('set___init__', args, targets,
                                            self.to_position(node, ctx),
                                            self.noinfo(ctx))
        return [constr_call], res_var.ref

    def translate_builtin_func(self, node: ast.Call, ctx) -> StmtAndExpr:
        """
        Translates a call to a builtin function like len() or isinstance()
        """
        if get_func_name(node) == 'isinstance':
            return self.translate_isinstance(node, ctx)
        elif get_func_name(node) == 'super':
            return self.translate_super(node, ctx)
        elif get_func_name(node) == 'len':
            return self.translate_len(node, ctx)
        elif get_func_name(node) == 'set':
            return self.translate_set(node, ctx)
        else:
            raise UnsupportedException(node)

    def translate_Call(self, node: ast.Call, ctx) -> StmtAndExpr:
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
            perm = self.viper.FullPerm(position, self.noinfo(ctx))
            return arg_stmts, self._create_predicate_access(target_name, args,
                                                            perm, node, ctx)
        elif target.pure:
            type = self.translate_type(target.type, ctx)
            return (arg_stmts, self.viper.FuncApp(target_name, args,
                                                  position,
                                                  self.noinfo(ctx),
                                                  type,
                                                  formal_args))
        else:
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
                errorvar = ctx.current_function.create_variable(
                    target.name + '_err',
                    ctx.program.classes['Exception'], self.translator)
                targets.append(errorvar.ref)
            call = [self.viper.MethodCall(target_name, args, targets,
                                          position,
                                          self.noinfo(ctx))]
            if target.declared_exceptions:
                call = call + self.create_exception_catchers(errorvar,
                    ctx.current_function.try_blocks, node, ctx)
            return (arg_stmts + call,
                    result_var.ref if result_var else None)