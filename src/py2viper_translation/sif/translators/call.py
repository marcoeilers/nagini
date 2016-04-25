import ast

from typing import List, Tuple, Optional

from py2viper_translation.lib.jvmaccess import JVM
from py2viper_translation.lib.typeinfo import TypeInfo
from py2viper_translation.lib.util import get_func_name, UnsupportedException, \
    InvalidProgramException
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import SIFPythonMethod
from py2viper_translation.translators.abstract import (
    Expr,
    Stmt,
    StmtsAndExpr,
    TranslatorConfig,
    )
from py2viper_translation.translators.call import CallTranslator


class CallResults:
    """
    Container for the results of an already translated call node.
    """
    def __init__(self):
        self._results = []
        self._idx = 0

    def next(self) -> Optional[Expr]:
        """
        Returns the next result expr or None if there are no more available.
        """
        res = None
        if self._idx < len(self._results):
            res = self._results[self._idx]
            self._idx += 1

        return res

    def add_result(self, result: Expr):
        self._results.append(result)


class SIFCallTranslator(CallTranslator):
    """
    SIF version of the CallTranslator.
    """
    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        # Map of already translated call nodes.
        self.translated_calls = {}  # Map[ast.Call, CallResults]

    def translate_method_call(self, target: SIFPythonMethod, args: List[Expr],
                              arg_stmts: List[Stmt],
                              position: 'silver.ast.Position', node: ast.AST,
                              ctx: SIFContext) -> StmtsAndExpr:
        assert node not in self.translated_calls
        call_results = CallResults()
        self.translated_calls[node] = call_results
        targets = []

        if ctx.current_function is None:
            if ctx.current_class is None:
                # global variable
                raise InvalidProgramException(node, 'purity.violated')
            else:
                # static field
                raise UnsupportedException(node)

        if target.type is not None:
            result_var = result_var = ctx.current_function.create_variable(
                target.name + '_res', target.type, self.translator)
            targets.append(result_var.ref)
            call_results.add_result(result_var.ref)
            targets.append(result_var.var_prime.ref)
            call_results.add_result(result_var.var_prime.ref)
        if target.declared_exceptions:
            raise UnsupportedException(node)
        # Add timeLevel to targets.
        targets.append(ctx.current_function.tl_var.ref)

        call = self.viper.MethodCall(target.sil_name, args, targets,
                                     position, self.no_info(ctx))
        res_expr = call_results.next() if target.type else None

        return arg_stmts + [call], res_expr

    def _translate_args(self, node: ast.Call,
                        ctx: SIFContext) -> Tuple[List[Stmt], List[Expr]]:
        args = []
        arg_stms = []
        for arg in node.args:
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            arg_stms += arg_stmt
            args.append(arg_expr)
            ctx.use_prime = True
            arg_stmt, arg_expr = self.translate_expr(arg, ctx)
            ctx.use_prime = False
            arg_stms += arg_stmt
            args.append(arg_expr)
        # Add timeLevel.
        assert ctx.current_function
        args.append(ctx.current_function.tl_var.ref)

        return arg_stms, args

    def _translate_receiver(self, node: ast.Call,
                            ctx: SIFContext) -> Tuple[List[Stmt], List[Expr]]:
        recv_stmt, recv = self.translate_expr(node.func.value, ctx)
        ctx.use_prime = True
        recv_stmt_p, recv_p = self.translate_expr(node.func.value, ctx)
        assert not recv_stmt_p
        ctx.use_prime = False

        # timeLevel := timeLevel || !(typeof(recv) == typeof(recv_p))
        type_expr = self.type_factory.type_equivalent(recv, recv_p, ctx)
        type_expr = self.viper.Not(type_expr, type_expr.pos(),
                                   type_expr.info())
        rhs = self.viper.Or(ctx.current_function.tl_var.ref,
                            type_expr,
                            self.no_position(ctx),
                            self.no_info(ctx))
        assign = self.viper.LocalVarAssign(ctx.current_function.tl_var.ref,
                                           rhs,
                                           self.no_position(ctx),
                                           self.no_info(ctx))
        return recv_stmt + [assign], [recv, recv_p]

    def translate_normal_call(self, node: ast.Call,
                              ctx: SIFContext) -> StmtsAndExpr:
        arg_stmts, args = self._translate_args(node, ctx)
        name = get_func_name(node)
        position = self.to_position(node, ctx)
        if name in ctx.program.classes:
            # this is a constructor call
            target_class = ctx.program.classes[name]
            return self._translate_constructor_call(target_class, node, args,
                                                    arg_stmts, ctx)
        if isinstance(node.func, ast.Attribute):
            # Method called on an object.
            recv_cls = self.get_type(node.func.value, ctx)
            target = recv_cls.get_func_or_method(node.func.attr)
            recv_stmts, recvs = self._translate_receiver(node, ctx)
            arg_stmts = recv_stmts + arg_stmts
            args = recvs + args
        else:
            # Global function/method called.
            recv_cls = None
            target = ctx.program.get_func_or_method(name)

        assert target, "Predicates not supported yet."
        if target.pure:
            raise UnsupportedException(node)

        return self.translate_method_call(target, args, arg_stmts,
                                          position, node, ctx)

    def translate_Call(self, node: ast.Call, ctx: SIFContext):
        """
        First checks in self.translated_calls of the call was already
        translated (returning the next result). Calls super().translate_Call
        if that isn't the case.
        """
        if node in self.translated_calls:
            # Sanity check. This can only happen if ctx.use_prime == True.
            assert ctx.use_prime
            return [], self.translated_calls[node].next()
        else:
            return super().translate_Call(node, ctx)


