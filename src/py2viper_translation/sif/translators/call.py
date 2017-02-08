import ast

from py2viper_contracts.contracts import CONTRACT_FUNCS
from py2viper_translation.lib.constants import BOOL_TYPE
from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.program_nodes import PythonClass, PythonType
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import (
    get_func_name,
    UnsupportedException,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.expr_cache import ExprCache
from py2viper_translation.sif.lib.program_nodes import SIFPythonMethod
from py2viper_translation.sif.translators.abstract import SIFTranslatorConfig
from py2viper_translation.sif.translators.func_triple_domain_factory import (
    FuncTripleDomainFactory as FTDF,
)
from py2viper_translation.translators.abstract import (
    Expr,
    Stmt,
    StmtsAndExpr,
)
from py2viper_translation.translators.call import CallTranslator
from typing import List, Tuple


class SIFCallTranslator(CallTranslator):
    """
    SIF version of the CallTranslator.
    """
    def __init__(self, config: SIFTranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        # Map of already translated call nodes.
        self.translated_calls = {}  # Map[ast.Call, ExprCache]

    def _translate_constructor_call(self, target_class: PythonClass,
            node: ast.Call, args: List, arg_stmts: List,
            ctx: SIFContext) -> StmtsAndExpr:
        info = self.no_info(ctx)
        call_results = self.translated_calls[node]
        res_var = ctx.current_function.create_variable(target_class.name +
                                                       '_res',
                                                       target_class,
                                                       self.translator)
        call_results.add_result(res_var.ref())
        call_results.add_result(res_var.var_prime.ref())
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

        return arg_stmts + stmts, call_results.next()

    def _translate_builtin_func(self, node: ast.Call,
                                ctx: SIFContext) -> StmtsAndExpr:
        raise UnsupportedException(node, "Built-ins not supported.")

    def _translate_function_call(self, target: SIFPythonMethod, args: List[Expr],
                                 formal_args: List[Expr], arg_stmts: List[Stmt],
                                 position: 'silver.ast.Position', node: ast.AST,
                                 ctx: SIFContext) -> StmtsAndExpr:
        assert not ctx.use_prime
        info = self.no_info(ctx)
        call_results = self.translated_calls[node]

        type_ = self.translate_type(target.type, ctx)
        func_app = self.viper.FuncApp(target.sil_name, args, position,
                                      info, type_, formal_args)
        # We have to update the current timeLevel var expression.
        tl_expr = self.config.func_triple_factory.get_call(FTDF.GET_TL,
            [func_app], target.type, position, info, ctx)
        ctx.current_tl_var_expr = tl_expr

        # Add the resulting expressions to call_results.
        res_expr = self.config.func_triple_factory.get_call(FTDF.GET,
            [func_app], target.type, position, info, ctx)
        res_expr_p = self.config.func_triple_factory.get_call(FTDF.GET_PRIME,
            [func_app], target.type, position, info, ctx)
        call_results.add_result(res_expr)
        call_results.add_result(res_expr_p)
        call_results.add_result(tl_expr)

        return arg_stmts, call_results.next()

    def _translate_method_call(self, target: SIFPythonMethod, args: List[Expr],
                               arg_stmts: List[Stmt],
                               position: 'silver.ast.Position', node: ast.AST,
                               ctx: SIFContext) -> StmtsAndExpr:
        call_results = self.translated_calls[node]
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
            call_results.add_result(result_var.ref())
            targets.append(result_var.var_prime.ref())
            call_results.add_result(result_var.var_prime.ref())
        if target.declared_exceptions:
            raise UnsupportedException(node)
        # Add timeLevel to targets.
        targets.append(ctx.current_function.new_tl_var.ref())

        call = self.create_method_call_node(
            ctx, target.sil_name, args, targets, position, self.no_info(ctx),
            target_method=target, target_node=node)
        res_expr = call_results.next() if target.type else None

        return arg_stmts + call, res_expr

    def _translate_args(self, node: ast.Call,
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
        recv_stmts, recv = self.translate_expr(node.func.value, ctx)
        with ctx.prime_ctx():
            recv_stmts_p, recv_p = self.translate_expr(node.func.value, ctx)
            assert not recv_stmts_p
        recv_type = self.get_type(node.func.value, ctx)

        # timeLevel := timeLevel || !(typeof(recv) == typeof(recv_p))
        type_expr = self.type_factory.type_comp(recv, recv_p, ctx)
        rhs = self.viper.Or(ctx.current_function.new_tl_var.ref(),
                            type_expr,
                            self.no_position(ctx),
                            info)
        assign = self.viper.LocalVarAssign(ctx.current_function.new_tl_var.ref(),
                                           rhs,
                                           self.no_position(ctx),
                                           info)
        return recv_stmts + [assign], [recv, recv_p], [recv_type, recv_type]

    def translate_Call(self, node: ast.Call, ctx: SIFContext) -> StmtsAndExpr:
        """
        First checks in self.translated_calls if the call was already
        translated (returning the next result). Calls super().translate_Call
        if that isn't the case.
        """
        func_name = get_func_name(node)
        if node in self.translated_calls:
            assert len(self.translated_calls[node])
            call_expr = self.translated_calls[node].next()
            if call_expr:
                return [], call_expr
        elif func_name in CONTRACT_FUNCS:
            # Contract functions need no ExprCache.
            return self.translate_contractfunc_call(node, ctx)

        self.translated_calls[node] = ExprCache()
        return super().translate_Call(node, ctx)
