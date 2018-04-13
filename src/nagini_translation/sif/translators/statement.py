"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.lib.typedefs import Expr, StmtsAndExpr
from nagini_translation.lib.util import (
    flatten,
    get_body_indices,
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.sif.lib.context import SIFContext
from nagini_translation.translators.abstract import Stmt
from nagini_translation.translators.statement import StatementTranslator
from typing import List, Tuple


class SIFStatementTranslator(StatementTranslator):
    """
    Secure Information Flow version of the StatementTranslator.
    """

    def translate_stmt(self, node: ast.AST, ctx: SIFContext) -> List[Stmt]:
        # New statement means we always updated the __new_tl var before, thus
        # we use that and reset the current TL var expression.
        ctx.current_tl_var_expr = None
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

        tl_stmts, if_cond = self._create_condition_and_timelevel_statements(
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
            raise UnsupportedException(
                node, "complex assignments not supported")

        # First translate assignment for normal variables.
        stmts = super().translate_stmt_Assign(node, ctx)
        # Translate assignment for prime variables.
        with ctx.prime_ctx():
            stmts += super().translate_stmt_Assign(node, ctx)

        if self._tl_needs_update(node, ctx):
            tl_assign = self.viper.LocalVarAssign(
                ctx.actual_function.new_tl_var.ref(), ctx.current_tl_var_expr,
                self.to_position(node, ctx), self.no_info(ctx))
            stmts.append(tl_assign)

        return stmts

    def _tl_needs_update(self, node: ast.Assign, ctx: SIFContext):
        """Return True if the timelevel needs to be updated after Assign."""
        # Update TL after call to a pure function (including magic functions).
        update_tl = isinstance(node.value, ast.Subscript)
        if isinstance(node.value, ast.Call):
            target = self.get_target(node.value, ctx)
            if isinstance(target, PythonMethod):
                update_tl = target.pure
        elif isinstance(node.value, ast.Compare):
            update_tl = isinstance(node.value.ops[0], (ast.In, ast.NotIn))
        # Except if the target is a subscript
        update_tl &= (not isinstance(node.targets[0], ast.Subscript))
        return update_tl

    def _assign_with_subscript(
            self, lhs: ast.Tuple, rhs: Expr, node: ast.AST,
            ctx: SIFContext, allow_impure=False) -> Tuple[List[Stmt], List[Expr]]:
        if isinstance(node.targets[0].slice, ast.ExtSlice):
            raise UnsupportedException(
                node, "assignment to slice not supported")
        if ctx.use_prime:
            return [], []
        # First we have to translate the rhs in the prime ctx, since the entire
        # assignment gets translated to one method call instead of the usual
        # multiple assignments.
        with ctx.prime_ctx():
            rhs_stmts_p, rhs_p = self.translate_expr(node.value, ctx)

        target_cls = self.get_type(lhs.value, ctx)
        lhs_stmts, target = self.translate_expr(lhs.value, ctx)
        idx_stmts, idx = self.translate_expr(
            lhs.slice.value, ctx, target_type=self.viper.Int)
        with ctx.prime_ctx():
            lhs_stmts_p, target_p = self.translate_expr(lhs.value, ctx)
            idx_stmts_p, idx_p = self.translate_expr(
                lhs.slice.value, ctx, target_type=self.viper.Int)
        args = [target, target_p, idx, idx_p, rhs, rhs_p,
                ctx.current_tl_var_expr]
        arg_types = [None] * 7
        call_targets = [ctx.actual_function.get_tl_var().ref()]
        setitem_stmts = self.get_method_call(
            target_cls, '__setitem__', args, arg_types, call_targets, node, ctx)

        # Build list of statements.
        res_stmts = []
        res_stmts.extend(rhs_stmts_p)
        res_stmts.extend(lhs_stmts)
        res_stmts.extend(lhs_stmts_p)
        res_stmts.extend(idx_stmts)
        res_stmts.extend(idx_stmts_p)
        res_stmts.extend(setitem_stmts)

        return res_stmts, []

    def translate_stmt_While(self, node: ast.While,
                             ctx: SIFContext) -> List[Stmt]:
        post_label = ctx.actual_function.get_fresh_name('post_loop')
        end_label = ctx.actual_function.get_fresh_name('loop_end')
        self.enter_loop_translation(node, post_label, end_label, ctx)
        tl_stmts, while_cond = self._create_condition_and_timelevel_statements(
            node.test, ctx)
        # Translate loop invariants.
        invariants = []
        for expr, aliases in ctx.actual_function.loop_invariants[node]:
            with ctx.additional_aliases(aliases):
                ctx.current_tl_var_expr = None
                invariant = self.translate_contract(expr, ctx)
                invariants.append(invariant)

        start, end = get_body_indices(node.body)
        var_types = self._get_havocked_var_type_info(node.body[start:end], ctx)
        invariants = var_types + invariants
        body = flatten([self.translate_stmt(stmt, ctx) for stmt in
                        node.body[start:end]])
        # Add timelevel statement at the end of the loop.
        body.extend(tl_stmts)
        loop_stmts = self.create_while_node(ctx, while_cond, invariants, [],
                                            body, node)
        self.leave_loop_translation(ctx)
        res = tl_stmts + loop_stmts
        return res

    def _get_havocked_var_type_info(self, nodes: List[ast.AST],
                                   ctx: SIFContext) -> List[Expr]:
        """
        Creates a list of assertions containing type information for all local
        variables written to within the given partial ASTs which already
        existed before.
        To be used to remember type information about arguments/local variables
        which are assigned to in loops and therefore havocked.
        """
        result = []
        vars = self._get_havocked_vars(nodes, ctx)
        for var in vars:
            result.append(self.type_check(var.ref(), var.type,
                                          self.no_position(ctx), ctx))
            result.append(self.type_check(var.var_prime.ref(), var.type,
                                          self.no_position(ctx), ctx))
        return result

    def _create_condition_and_timelevel_statements(
            self, condition: ast.AST, ctx: SIFContext) -> StmtsAndExpr:
        """
        Creates the timelevel statement before ifs and whiles.

        Returns:
            List of statements for the timelevel update and the translated
            condition.
        """
        pos = self.to_position(condition, ctx)
        info = self.no_info(ctx)
        # Translate condition twice, once normally and once in the prime ctx.
        cond_stmts, cond = self.translate_expr(condition, ctx,
                                               target_type=self.viper.Bool)
        with ctx.prime_ctx():
            cond_stmts_p, cond_p = self.translate_expr(
                condition, ctx, target_type=self.viper.Bool)
        # tl := tl || cond != cond_p
        cond_cmp = self.viper.NeCmp(cond, cond_p, pos, info)
        or_expr = self.viper.Or(ctx.current_tl_var_expr, cond_cmp, pos, info)
        tl_assign = self.viper.LocalVarAssign(
            ctx.actual_function.new_tl_var.ref(), or_expr, pos, info)

        if cond_stmts or cond_stmts_p:
            raise InvalidProgramException(condition, 'purity.violated')

        return cond_stmts + cond_stmts_p + [tl_assign], cond

    def _translate_return(self, node: ast.Return,
                          ctx: SIFContext) -> List[Stmt]:
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        rhs_stmt, rhs = self.translate_expr(node.value, ctx)
        with ctx.prime_ctx():
            rhs_stmt_p, rhs_p = self.translate_expr(node.value, ctx)
        assign = self.viper.LocalVarAssign(
            ctx.current_function.result.ref(node, ctx), rhs, pos, info)
        assign_p = self.viper.LocalVarAssign(
            ctx.current_function.result.var_prime.ref(), rhs_p, pos, info)
        res = rhs_stmt + [assign] + rhs_stmt_p + [assign_p]
        if isinstance(node.value, ast.Call):
            _, tl_expr = self.translate_expr(node.value, ctx)
            assign_tl = self.viper.LocalVarAssign(
                ctx.current_function.new_tl_var.ref(),
                self.to_bool(tl_expr, ctx), pos, info)
            res.append(assign_tl)

        return res
