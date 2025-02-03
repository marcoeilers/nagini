"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast

from nagini_translation.lib.constants import (
    BOOL_TYPE,
    FLOAT_TYPE,
    INT_TYPE,
    PSET_TYPE,
    PSEQ_TYPE,
    STRING_TYPE,
    TUPLE_TYPE
)
from nagini_translation.lib.program_nodes import MethodType
from nagini_translation.lib.typedefs import StmtsAndExpr, Info
from nagini_translation.lib.util import (
    InvalidProgramException,
    UnsupportedException,
)
from nagini_translation.sif.lib.util import (
    in_override_check,
    in_postcondition_of_dyn_bound_call,
)
from nagini_translation.translators.abstract import Context
from nagini_translation.translators.contract import ContractTranslator


class SIFContractTranslator(ContractTranslator):
    """
    Extended AST version of the contract translator.
    """
    def _create_dyn_check_info(self, ctx: Context) -> Info:
        """
        Check if we are in the postcondition of a method which calls will be dynamically
        bound, if so create a SIFDynCheckInfo, else NoInfo.
        If we are in a override check method, only do the version with dynamic call check.
        """
        self_type = in_postcondition_of_dyn_bound_call(self.type_factory, ctx)
        if self_type:
            return self.viper.SIFDynCheckInfo([], self_type,
                                              dyn_check_only=in_override_check(ctx))
        return self.no_info(ctx)


    def translate_low(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Low() contract function.
        """
        if len(node.args) != 1:
            raise UnsupportedException(node, "Low() requires exactly one argument")
        stmts, expr = self.translate_expr(node.args[0], ctx)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        info = self._create_dyn_check_info(ctx)
        return [], self.viper.Low(
            expr, None, self.to_position(node, ctx), info)

    def translate_lowval(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the Low() contract function.
        """
        stmts, expr = self.translate_expr(node.args[0], ctx)
        if stmts:
            raise InvalidProgramException(node, 'purity.violated')
        info = self._create_dyn_check_info(ctx)
        # determine the comparator function to use
        expr_type = self.get_type(node.args[0], ctx)
        low_val_types = [BOOL_TYPE, FLOAT_TYPE, INT_TYPE, PSET_TYPE, PSEQ_TYPE,
                         STRING_TYPE, TUPLE_TYPE]
        if expr_type.name in low_val_types:
            comparator = expr_type.get_function('__eq__')
            comparator = comparator.sil_name
        else:
            comparator = None
        return [], self.viper.Low(
            expr, comparator, self.to_position(node, ctx), info)

    def translate_lowevent(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the LowEvent() contract function.
        """
        if ctx.current_class and ctx.current_function.method_type == MethodType.normal:
            self_type = self.type_factory.typeof(
                next(iter(ctx.actual_function.args.values())).ref(), ctx)
            info = self.viper.SIFDynCheckInfo([], self_type,
                                              dyn_check_only=in_override_check(ctx))
        else:
            info = self.no_info(ctx)
        if ctx.sif == 'prob':
            # LowEvent is trivially true
            res = self.viper.TrueLit(self.to_position(node, ctx), info)
        else:
            res = self.viper.LowEvent(self.to_position(node, ctx), info)
        return [], res

    def translate_lowexit(self, node: ast.Call, ctx: Context) -> StmtsAndExpr:
        """
        Translates a call to the LowExit() contract function.
        """
        info = self.no_info(ctx)
        return [], self.viper.LowExit(self.to_position(node, ctx), info)

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
        cond_stmts, cond = self.translate_expr(node.args[0], ctx,
                                               target_type=self.viper.Bool)
        if cond_stmts:
            raise InvalidProgramException(node, 'purity.violated')
        must_terminate = super().translate_terminates_sif(node, ctx)
        pos = self.to_position(node, ctx)
        info = self.no_info(ctx)
        implication = self.viper.Implies(cond, must_terminate[1], pos, info)
        terminates_exp = self.viper.TerminatesSif(cond, pos, info)
        return must_terminate[0], self.viper.And(implication, terminates_exp, pos, info)
