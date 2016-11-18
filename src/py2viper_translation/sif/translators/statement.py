import ast

from py2viper_translation.lib.typedefs import StmtsAndExpr
from py2viper_translation.lib.util import (
    flatten,
    get_body_start_index,
    InvalidProgramException,
    UnsupportedException,
)
from py2viper_translation.sif.lib.context import SIFContext
from py2viper_translation.translators.abstract import Expr, Stmt
from py2viper_translation.translators.statement import StatementTranslator
from typing import List, Tuple


class SIFStatementTranslator(StatementTranslator):
    """
    Secure Information Flow version of the StatementTranslator.
    """

    def translate_stmt(self, node: ast.AST, ctx: SIFContext) -> List[Stmt]:
        return super().translate_stmt(node, ctx)

    def translate_stmt_If(self, node: ast.If, ctx: SIFContext) -> List[Stmt]:
        """
        SIF translation of if-statements.

        ```
        #!rst

        Python:
            if cond:
                then_body
            else:
                else_body

        Silver:

        .. code-block:: silver
            tl = tl || cond != cond_p
            if(cond) {
                sif(then_body)
            } else {
                sif(else_body)
            }
        ```
        """
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)

        tl_stmts, if_cond = self._create_condition_timelevel_statements(
            node.test, ctx)

        # Translate the bodies.
        then_body = flatten([self.translate_stmt(stmt, ctx)
                             for stmt in node.body])
        then_block = self.translate_block(then_body, pos, info)
        else_body = flatten([self.translate_stmt(stmt, ctx)
                             for stmt in node.orelse])
        else_block = self.translate_block(else_body, pos, info)
        if_stmt = self.viper.If(if_cond, then_block, else_block, pos, info)

        return tl_stmts + [if_stmt]

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

        return stmts

    def translate_stmt_While(self, node: ast.While,
                             ctx: SIFContext) -> List[Stmt]:
        self.enter_loop_translation(node, ctx)
        tl_stmts, while_cond = self._create_condition_timelevel_statements(
            node.test, ctx)
        # Translate loop invariants.
        invariants = []
        for expr, aliases in ctx.actual_function.loop_invariants[node]:
            with ctx.additional_aliases(aliases):
                invariants.append(self.translate_contract(expr, ctx))

        # Reset timelevel expression.
        ctx.current_tl_var_expr = None

        body_index = get_body_start_index(node.body)
        body = flatten([self.translate_stmt(stmt, ctx) for stmt in
                        node.body[body_index:]])
        # Add timelevel statement at the end of the loop.
        body.extend(tl_stmts)
        loop_stmts = self.create_while_node(ctx, while_cond, invariants, [],
                                            body, node)
        self.leave_loop_translation(ctx)
        res = tl_stmts + loop_stmts
        return res

    def _create_condition_timelevel_statements(self, condition: ast.AST,
                                               ctx: SIFContext) -> StmtsAndExpr:
        """Creates the timelevel statement before ifs and whiles.

        Returns:
            List of statements for the timelevel update and the translated
            condition.
        """
        pos = self.no_position(ctx)
        info = self.no_info(ctx)
        # Translate condition twice, once normally and once in the prime ctx.
        cond_stmts, cond = self.translate_to_bool(condition, ctx)
        ctx.set_prime_ctx()
        cond_stmts_p, cond_p = self.translate_to_bool(condition, ctx)
        ctx.set_normal_ctx()
        # tl := tl || cond != cond_p
        cond_cmp = self.viper.NeCmp(cond, cond_p, pos, info)
        or_expr = self.viper.Or(ctx.current_tl_var_expr, cond_cmp, pos, info)
        tl_assign = self.viper.LocalVarAssign(
            ctx.actual_function.new_tl_var.ref(), or_expr, pos, info)
        # After this the current_tl_expr is always reset.
        ctx.current_tl_var_expr = None

        if cond_stmts or cond_stmts_p:
            raise InvalidProgramException(condition, 'purity.violated')

        return cond_stmts + cond_stmts_p + [tl_assign], cond

    def _translate_return(self, node: ast.Return,
                          ctx: SIFContext) -> List[Stmt]:
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        ctx.set_prime_ctx()
        rhs_stmt_p, rhs_p = self.translate_expr(node.value, ctx)
        ctx.set_normal_ctx()
        assign = self.viper.LocalVarAssign(
            ctx.current_function.result.ref(node, ctx), rhs, pos, info)
        assign_p = self.viper.LocalVarAssign(
            ctx.current_function.result.var_prime.ref(), rhs_p, pos, info)
        res = rhs_stmt + [assign] + rhs_stmt_p + [assign_p]
        if isinstance(node.value, ast.Call):
            _, tl_expr = self.translate_expr(node.value, ctx)
            assign_tl = self.viper.LocalVarAssign(
                ctx.current_function.new_tl_var.ref(), tl_expr, pos, info)
            res.append(assign_tl)

        return res
