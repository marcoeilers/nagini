"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Wait-level translator."""


import ast
import operator

from typing import Union

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.context import Context
from nagini_translation.lib.jvmaccess import JVM
from nagini_translation.lib.program_nodes import PythonVar
from nagini_translation.lib.typedefs import (
    StmtsAndExpr,
)
from nagini_translation.lib.typeinfo import TypeInfo
from nagini_translation.lib.viper_ast import ViperAST
from nagini_translation.translators.abstract import TranslatorConfig
from nagini_translation.translators.common import CommonTranslator
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)


class WaitLevelTranslator(CommonTranslator):
    """Class for translating wait-levels."""

    def __init__(self, config: TranslatorConfig, jvm: JVM, source_file: str,
                 type_info: TypeInfo, viper_ast: ViperAST,
                 obligation_manager: ObligationManager) -> None:
        super().__init__(config, jvm, source_file, type_info, viper_ast)
        self._obligation_manager = obligation_manager

    def is_wait_level_comparison(self, node: ast.Compare,
                                 ctx: Context) -> bool:
        """Check if we are comparing with ``WaitLevel``.

        Allowed forms are:

        1.  ``WaitLevel() < Level(l)``
        2.  ``Level(l1) < Level(l2)``
        """
        return (len(node.ops) == 1 and
                isinstance(node.ops[0], ast.Lt) and
                len(node.comparators) == 1 and
                isinstance(node.left, ast.Call) and
                isinstance(node.left.func, ast.Name) and
                (node.left.func.id in ('WaitLevel', 'Level')) and
                isinstance(node.comparators[0], ast.Call) and
                isinstance(node.comparators[0].func, ast.Name) and
                node.comparators[0].func.id == 'Level')

    def translate_wait_level_comparison(self, node: ast.Compare,
                                        ctx: Context) -> StmtsAndExpr:
        """Translate wait-level comparison.

        Comparisons can be in one of the following forms:

        1.  ``WaitLevel() < Level()``
        2.  ``Level() < Level()``
        """
        assert self.is_wait_level_comparison(node, ctx)
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        expr_right = self._translate_level(node.comparators[0])

        if node.left.func.id == 'Level':
            expr_left = self._translate_level(node.left)
            expression = sil.PermLtCmp(expr_left, expr_right)
        elif ctx.obligation_context.is_translating_loop():
            expression = self._translate_waitlevel_loop(
                expr_right, node, ctx)
        else:
            expression = self._translate_waitlevel_method(
                expr_right, node, ctx)
        return ([], expression.translate(self, ctx, position, info))

    def _translate_level(self, node: ast.Call) -> sil.PermExpression:
        """Translate a call to ``Level``."""
        assert len(node.args) == 1
        arg = sil.PythonRefExpression(node.args[0])
        return self.create_level_call(arg)

    def create_level_call(self, expr: sil.RefExpression) -> sil.PermExpression:
        return sil.PermCall('Level', [sil.CallArg('r', sil.REF, expr)])

    def _create_level_op(
            self, expr: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context,
            oper: Union[operator.le, operator.lt]) -> sil.BoolExpression:
        obligation = self._obligation_manager.must_release_obligation
        fields = obligation.create_fields_untranslated()
        var = ctx.current_function.create_variable(
            '_r', ctx.module.global_module.classes['object'],
            self.translator, local=False)
        op = oper(self.create_level_call(sil.RefVar(var)), expr)
        for_perms = [sil.ForPerm(var.sil_name, f, op) for f in fields]
        return sil.BigAnd(for_perms + [oper(residue_level_var, expr)])

    def create_level_below(
            self, expr: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        return self._create_level_op(expr, residue_level_var, ctx, operator.lt)

    def _create_level_below_equal(
            self, expr: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        return self._create_level_op(expr, residue_level_var, ctx, operator.le)

    def initialize_current_wait_level(
            self, current_wait_level: sil.PermExpression,
            residue_level_var: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        return sil.InhaleExhale(
            self._create_level_below_equal(
                current_wait_level,
                residue_level_var,
                ctx),
            sil.TrueLit())

    def _create_level_below_inex(
            self, guard: sil.BoolExpression, expr: sil.PermExpression,
            level: PythonVar, ctx: Context) -> sil.BoolExpression:
        return sil.InhaleExhale(
            sil.TrueLit(),
            sil.Implies(
                guard,
                self.create_level_below(
                    expr,
                    sil.PermVar(level),
                    ctx)))

    def _translate_waitlevel_loop(
            self, expr: sil.PermExpression, node: ast.Compare,
            ctx: Context) -> sil.BoolExpression:
        """Translate ``WaitLevel() < Level()`` in loop invariant."""
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        obligation_info = ctx.obligation_context.current_loop_info
        guard = obligation_info.get_wait_level_guard(node.left)
        context_info = ctx.obligation_context.get_surrounding_loop_info()
        if context_info:
            context_residue_level = context_info.residue_level
        else:
            method_info = ctx.current_function.obligation_info
            context_residue_level = method_info.residue_level
        body_inhale = sil.Inhale(
            sil.Implies(
                guard,
                sil.PermVar(obligation_info.residue_level) < expr))
        obligation_info.prepend_body(
            body_inhale.translate(self, ctx, position, info))
        body_exhale = sil.Implies(
            sil.Not(sil.BoolVar(obligation_info.loop_check_before_var)),
            self._create_level_below_inex(
                guard, expr, obligation_info.residue_level, ctx))
        obligation_info.add_invariant(
            body_exhale.translate(self, ctx, position, info))
        context_inhale = sil.Inhale(
            sil.Implies(
                guard,
                sil.PermVar(context_residue_level) < expr))
        obligation_info.append_after_loop(
            context_inhale.translate(self, ctx, position, info))
        context_exhale = sil.Implies(
            sil.BoolVar(obligation_info.loop_check_before_var),
            self._create_level_below_inex(
                guard, expr, context_residue_level, ctx))
        obligation_info.add_invariant(
            context_exhale.translate(self, ctx, position, info))
        return sil.TrueLit()

    def _translate_waitlevel_method(
            self, expr: sil.PermExpression, node: ast.Compare,
            ctx: Context) -> sil.BoolExpression:
        """Translate ``WaitLevel() < Level()`` in method contract."""
        position = self.to_position(node, ctx)
        info = self.no_info(ctx)

        obligation_info = ctx.actual_function.obligation_info
        guard = obligation_info.get_wait_level_guard(node.left)
        exhale = self._create_level_below_inex(
            guard, expr, obligation_info.residue_level, ctx)
        translated_exhale = exhale.translate(self, ctx, position, info)
        if ctx.ignore_waitlevel_constraints or obligation_config.disable_waitlevel_check:
            return sil.TrueLit()
        if ctx.obligation_context.is_translating_posts:
            obligation_info.add_postcondition(translated_exhale)
            caller_inhale = sil.InhaleExhale(
                sil.PermVar(obligation_info.current_wait_level) < expr,
                sil.TrueLit())
            return caller_inhale
        else:
            obligation_info.add_precondition(translated_exhale)
            body_inhale = sil.InhaleExhale(
                sil.PermVar(obligation_info.residue_level) < expr,
                sil.TrueLit())
            return body_inhale
