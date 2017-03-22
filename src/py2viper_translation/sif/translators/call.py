import ast

from py2viper_translation.lib.constants import (
    BOOL_TYPE,
    PRIMITIVE_BOOL_TYPE,
    PRIMITIVE_INT_TYPE,
)
from py2viper_translation.lib.program_nodes import PythonClass, PythonType
from py2viper_translation.lib.util import (
    get_func_name,
    UnsupportedException,
)
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.expr_cache import ExprCacheMixin
from py2viper_translation.sif.lib.program_nodes import SIFPythonMethod
from py2viper_translation.translators.abstract import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.translators.call import CallTranslator
from typing import List, Optional, Tuple


class SIFCallTranslator(CallTranslator, ExprCacheMixin):
    """
    SIF version of the CallTranslator.
    """
    def __init__(self, *args, **kwargs) -> None:
        CallTranslator.__init__(self, *args, **kwargs)
        ExprCacheMixin.__init__(self)

    def translate_constructor_call(
            self, target_class: PythonClass, node: ast.Call, args: List,
            arg_stmts: List, ctx: SIFContext) -> StmtsAndExpr:
        info = self.no_info(ctx)
        res_var = ctx.current_function.create_variable(
            target_class.name + '_res', target_class, self.translator)
        self._cache_results(node, [res_var.var_prime.ref()])
        fields = []
        for field in target_class.all_fields:
            fields.append(field.sil_field)
            fields.append(field.field_prime.sil_field)
        new_stmt = self.viper.NewStmt(res_var.ref(), fields,
                                      self.no_position(ctx),
                                      info)
        result_has_type = self._var_concrete_type_check(res_var.name,
                                                        target_class,
                                                        self.no_position(ctx),
                                                        ctx)
        # inhale the type information about the newly created object
        # so that it's already present when calling __init__.
        type_inhale = self.viper.Inhale(result_has_type, self.no_position(ctx),
                                        info)
        # Set the prime version to be equal to the newly created var.
        assign = self.viper.LocalVarAssign(res_var.var_prime.ref(),
                                           res_var.ref(),
                                           self.no_position(ctx),
                                           info)
        args = [res_var.ref(), res_var.var_prime.ref()] + args
        stmts = [new_stmt, type_inhale, assign]
        target = target_class.get_method('__init__')
        if target:
            targets = []
            if target.declared_exceptions:
                raise UnsupportedException(node, "Exceptions not supported.")
            # Add timeLevel to targets.
            targets.append(ctx.current_function.new_tl_var.ref())
            init = self.create_method_call_node(
                ctx, target.sil_name, args, targets,
                self.to_position(node, ctx), info,
                target_method=target, target_node=node)
            stmts.extend(init)

        return arg_stmts + stmts, res_var.ref()

    def _translate_builtin_func(self, node: ast.Call,
                                ctx: SIFContext) -> StmtsAndExpr:
        func_name = get_func_name(node)
        if func_name == 'len':
            return self._translate_len(node, ctx)
        raise UnsupportedException(
            node, "Built-in not supported: %s" % func_name)

    def _translate_len(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        assert len(node.args) == 1
        stmts, target = self.translate_expr(node.args[0], ctx)
        with ctx.prime_ctx():
            stmts_p, target_p = self.translate_expr(node.args[0], ctx)
        arg_type = self.get_type(node.args[0], ctx)
        args = [target, target_p, ctx.current_tl_var_expr]
        arg_types = [arg_type, arg_type,
                     ctx.module.global_module.classes[PRIMITIVE_BOOL_TYPE]]
        func_app = self.get_function_call(
            arg_type, '__len__', args, arg_types, node, ctx)
        res_expr, res_expr_p, tl_expr = \
            self.config.func_triple_factory.extract_results(
                func_app, ctx.module.global_module.classes[PRIMITIVE_INT_TYPE],
                self.to_position(node, ctx), self.no_info(ctx), ctx)
        ctx.current_tl_var_expr = tl_expr
        self._cache_results(node, [res_expr_p, tl_expr])

        return stmts + stmts_p, res_expr

    def _translate_function_call(
            self, target: SIFPythonMethod, args: List[Expr],
            formal_args: List[Expr], arg_stmts: List[Stmt],
            position: 'silver.ast.Position', node: ast.AST,
            ctx: SIFContext) -> StmtsAndExpr:
        assert not ctx.use_prime
        info = self.no_info(ctx)
        type_ = self.translate_type(target.type, ctx)
        func_app = self.viper.FuncApp(target.sil_name, args, position,
                                      info, type_, formal_args)
        res_expr, res_expr_p, tl_expr = \
            self.config.func_triple_factory.extract_results(
                func_app, target.type, position, info, ctx)
        ctx.current_tl_var_expr = tl_expr
        self._cache_results(node, [res_expr_p, tl_expr])

        return arg_stmts, res_expr

    def _translate_method_call(self, target: SIFPythonMethod, args: List[Expr],
                               arg_stmts: List[Stmt],
                               position: 'silver.ast.Position', node: ast.AST,
                               ctx: SIFContext) -> StmtsAndExpr:
        targets = []
        if ctx.current_function is None:
            if ctx.current_class is None:
                # global variable
                raise UnsupportedException(node, "Global function call "
                                           "not supported.")
            else:
                # static field
                raise UnsupportedException(node, "Static fields not supported.")

        if target.type is not None:
            result_var = ctx.current_function.create_variable(
                target.name + '_res', target.type, self.translator)
            targets.append(result_var.ref())
            targets.append(result_var.var_prime.ref())
            self._cache_results(
                node, [result_var.ref(), result_var.var_prime.ref()])
        if target.declared_exceptions:
            raise UnsupportedException(node, 'Exceptions not supported.')
        # Add timeLevel to targets.
        targets.append(ctx.current_function.new_tl_var.ref())

        call = self.create_method_call_node(
            ctx, target.sil_name, args, targets, position, self.no_info(ctx),
            target_method=target, target_node=node)
        res_expr = self._try_cache(node)

        return arg_stmts + call, res_expr

    def _translate_call_args(self, node: ast.Call,
                        ctx: SIFContext) -> Tuple[List[Stmt], List[Expr],
                                                  List[PythonType]]:
        args = []
        arg_stmts = []
        arg_types = []
        for arg in node.args:
            arg_stmts, args, arg_types = self._translate_one_arg(arg, args,
                arg_stmts, arg_types, ctx)
            with ctx.prime_ctx():
                arg_stmts, args, arg_types = self._translate_one_arg(arg, args,
                    arg_stmts, arg_types, ctx)
        # Add timeLevel.
        assert ctx.current_function
        args.append(ctx.current_tl_var_expr)
        arg_types.append(ctx.module.global_module.classes[BOOL_TYPE])

        return arg_stmts, args, arg_types

    def _translate_one_arg(self, arg: Expr, args: List[Expr],
            arg_stmts: List[Stmt], arg_types: List[PythonType],
            ctx: SIFContext) -> Tuple[List[Stmt], List[Expr], List[PythonType]]:
        arg_stmt, arg_expr = self.translate_expr(arg, ctx)
        arg_type = self.get_type(arg, ctx)
        arg_stmts += arg_stmt
        args.append(arg_expr)
        arg_types.append(arg_type)
        return arg_stmts, args, arg_types

    def _translate_receiver(self, node: ast.Call, target: SIFPythonMethod,
            ctx: SIFContext) -> Tuple[List[Stmt], List[Expr], List[PythonType]]:
        info = self.no_info(ctx)
        position = self.to_position(node, ctx)
        recv_stmts, recv = self.translate_expr(node.func.value, ctx)
        with ctx.prime_ctx():
            recv_stmts_p, recv_p = self.translate_expr(node.func.value, ctx)
            assert not recv_stmts_p
        recv_type = self.get_type(node.func.value, ctx)

        # timeLevel := timeLevel || !(typeof(recv) == typeof(recv_p))
        type_expr = self.type_factory.type_comp(recv, recv_p, ctx)
        rhs = self.viper.Or(
            ctx.current_function.new_tl_var.ref(), type_expr, position, info)
        assign = self.viper.LocalVarAssign(
            ctx.current_function.new_tl_var.ref(), rhs, position, info)
        return recv_stmts + [assign], [recv, recv_p], [recv_type, recv_type]

    def translate_Call(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        """
        First checks in self.translated_calls if the call was already
        translated (returning the next result). Calls super().translate_Call
        if that isn't the case.
        """
        call_expr = self._try_cache(node)
        if call_expr:
            return [], call_expr

        return super().translate_Call(node, ctx)
