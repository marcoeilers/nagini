import ast

from py2viper_translation.lib.util import UnsupportedException
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.sif.lib.program_nodes import SIF_VAR_SUFFIX
from py2viper_translation.translators.abstract import Stmt
from py2viper_translation.translators.statement import StatementTranslator
from typing import List


class SIFStatementTranslator(StatementTranslator):
    """
    Secure Information Flow version of the StatementTranslator.
    """
    def translate_stmt(self, node: ast.AST, ctx: SIFContext) -> List[Stmt]:
        # Reset context to clear artifacts of translations from previous
        # statements.
        ctx.reset()
        return super().translate_stmt(node, ctx)

    def translate_stmt_Assign(self, node: ast.Assign,
                              ctx: SIFContext) -> List[Stmt]:
        if len(node.targets) != 1:
            raise UnsupportedException(node)
        if isinstance(node.targets[0], ast.Subscript):
            raise UnsupportedException(node)
        
        # First translate assignment for normal variables.
        stmts = super().translate_stmt_Assign(node, ctx)
        ctx.set_prime_ctx()
        # Translate assignment for prime variables.
        stmts += super().translate_stmt_Assign(node, ctx)
        ctx.set_normal_ctx()

        if ctx.current_tl_var_expr != ctx.current_function.new_tl_var.ref:
            # RHS was a function call. Need assignment for timeLevel
            assert isinstance(node.value, ast.Call)
            assign = self.viper.LocalVarAssign(
                ctx.current_function.new_tl_var.ref, ctx.current_tl_var_expr,
                self.to_position(node, ctx), self.no_info(ctx))
            ctx.current_tl_var_expr = None
            stmts.append(assign)

        return stmts

    def _translate_return(self, node: ast.Return,
                          ctx: SIFContext) -> List[Stmt]:
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        ctx.set_prime_ctx()
        rhs_stmt_p, rhs_p = self.translate_expr(node.value, ctx)
        ctx.set_normal_ctx()
        assign = self.viper.LocalVarAssign(
            ctx.current_function.result.ref, rhs, pos, info)
        assign_p = self.viper.LocalVarAssign(
            ctx.current_function.result.var_prime.ref, rhs_p, pos, info)
        res = rhs_stmt + [assign] + rhs_stmt_p + [assign_p]
        if isinstance(node.value, ast.Call):
            _, tl_expr = self.translate_expr(node.value, ctx)
            assign_tl = self.viper.LocalVarAssign(
                ctx.current_function.new_tl_var.ref, tl_expr, pos, info)
            res.append(assign_tl)

        return res




