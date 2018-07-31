"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
from typing import Optional

from nagini_translation.lib.constants import (
    BOOL_TYPE,
    FLOAT_TYPE,
    INT_TYPE,
    PSET_TYPE,
    SEQ_TYPE,
    STRING_TYPE,
    TUPLE_TYPE
)
from nagini_translation.lib.program_nodes import PythonMethod, MethodType
from nagini_translation.lib.typedefs import StmtsAndExpr, DomainFuncApp
from nagini_translation.lib.util import (InvalidProgramException,
                                         UnsupportedException)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.contract import ContractTranslator


class ExtendedASTContractTranslator(ContractTranslator):
    """
    Extended AST version of the contract translator.
    """

    def _is_in_postcondition(self, node: ast.Expr, func: PythonMethod) -> bool:
        post = func.postcondition
        for cond in post:
            for cond_node in ast.walk(cond[0]):
                if cond_node is node:
                    return True
        return False

    def _in_postcondition_of_dyn_bound_call(self, ctx: Context) -> Optional[DomainFuncApp]:
        """
        Determine if we are in a postcondition of a dynamically bound method.
        """
        if (ctx.current_class and
                ctx.current_function.method_type == MethodType.normal and
                ctx.obligation_context.is_translating_posts):
            return self.type_factory.typeof(
                next(iter(ctx.actual_function.args.values())).ref(), ctx)
        return None

    def translate_low(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Low() contract function.
        """
        if len(node.args) != 1:
            raise UnsupportedException(node, "Low() requires exactly one argument")
        stmts, expr = self.translate_expr(node.args[0], ctx)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        self_type = self._in_postcondition_of_dyn_bound_call(ctx)
        return [], self.viper.Low(
            expr, None, self_type, self.to_position(node, ctx), self.no_info(ctx))

    def translate_lowval(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Low() contract function.
        """
        stmts, expr = self.translate_expr(node.args[0], ctx)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        self_type = self._in_postcondition_of_dyn_bound_call(ctx)
        # determine the comparator function to use
        expr_type = self.get_type(node.args[0], ctx)
        low_val_types = [BOOL_TYPE, FLOAT_TYPE, INT_TYPE, PSET_TYPE, SEQ_TYPE,
                         STRING_TYPE, TUPLE_TYPE]
        if expr_type.name in low_val_types:
            comparator = expr_type.get_function('__eq__')
            comparator = comparator.sil_name
        else:
            comparator = None
        return [], self.viper.Low(
            expr, comparator, self_type, self.to_position(node, ctx), self.no_info(ctx))

    def translate_lowevent(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the LowEvent() contract function.
        """
        if ctx.current_class and ctx.current_function.method_type == MethodType.normal:
            self_type = self.type_factory.typeof(
                next(iter(ctx.actual_function.args.values())).ref(), ctx)
        else:
            self_type = None
        return [], self.viper.LowEvent(self_type, self.to_position(node, ctx), self.no_info(ctx))

    def translate_declassify(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Declassify() contract function.
        """
        stmts, expr = self.translate_expr(node.args[0], ctx)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        return [self.viper.Declassify(
            expr, self.to_position(node, ctx), self.no_info(ctx))], None

    def translate_terminates_sif(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the TerminatesSif() contract function.
        """
        cond_stmts, cond = self.translate_expr(node.args[0], ctx, target_type=self.viper.Bool)
        # rank_stmts, rank = self.translate_expr(node.args[1], ctx, target_type=self.viper.Int)
        if cond_stmts: # or rank_stmts:
            raise InvalidProgramException(node, 'purity.violated')
        return [], self.viper.TerminatesSif(
            cond, self.to_position(node, ctx), self.no_info(ctx))
