"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import ast
import copy
import operator
from typing import List

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.config import obligation_config
from nagini_translation.lib.constants import (
    GET_ARG_FUNC,
    GET_METHOD_FUNC,
    GET_OLD_FUNC,
    JOINABLE_FUNC,
    METHOD_ID_DOMAIN,
    OBJECT_TYPE,
    THREAD_DOMAIN,
    THREAD_POST_PRED,
)
from nagini_translation.lib.context import Context
from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Stmt
)
from nagini_translation.lib.util import (
    InvalidProgramException,
    OldExpressionCollector,
    OldExpressionTransformer,
    pprint,
)
from nagini_translation.translators.obligation.manager import (
    ObligationManager,
)
from nagini_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)


class ObligationMethodForkConstructor(StatementNodeConstructorBase):
    """A class that creates a method call node with obligation stuff."""

    def __init__(
            self, targets, thread: Expr,
            position: Position, info: Info,
            translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager,
            target_node: ast.AST) -> None:
        super().__init__(
            translator, ctx, obligation_manager, position, info,
            target_node)
        self._statements = []
        self._targets = targets
        self._method_statements = {}
        self._thread = thread
        self._target_node = target_node
        self.viper = self._translator.viper

    def construct_fork(self) -> None:
        """Construct statements to perform a call."""
        self._add_precondition_exhales()
        self._add_waitlevel()

    def _create_join_permission(self, method: PythonMethod) -> Expr:
        """
        Creates an assertion representing a permission to join the thread and the
        ThreadPost predicate if the target method terminates.
        """
        tcond = method.obligation_info.create_termination_check(True)
        tcond = tcond.translate(self._translator, self._ctx, self._position,
                                self._info)

        joinable_func = self.viper.FuncApp(JOINABLE_FUNC, [self._thread],
                                           self._position, self._info,
                                           self.viper.Bool)
        post_pred_acc = self.viper.PredicateAccess([self._thread], THREAD_POST_PRED,
                                                   self._position, self._info)
        full_perm = self.viper.FullPerm(self._position, self._info)
        post_pred = self.viper.PredicateAccessPredicate(post_pred_acc, full_perm,
                                                        self._position, self._info)
        joinable = self.viper.And(joinable_func, post_pred, self._position,
                                  self._info)
        joinable = self.viper.Implies(tcond, joinable, self._position, self._info)
        return joinable

    def _remember_old_expressions(self, method: PythonMethod,
                                  collector: OldExpressionCollector) -> Expr:
        """
        Creates an assertion that connects all old expressions in the method's
        postcondition to the thread object.
        """
        old_info = self.viper.TrueLit(self._position, self._info)
        normalizer = OldExpressionTransformer()
        normalizer.arg_names = [arg for arg in method._args]
        for expr in collector.expressions:
            print_expr = normalizer.visit(copy.deepcopy(expr))
            name = pprint(print_expr)
            id = self.viper.IntLit(self._translator._get_string_value(name),
                                   self._position, self._info)
            old_func = self.viper.DomainFuncApp(GET_OLD_FUNC, [self._thread, id],
                                                self.viper.Ref, self._position,
                                                self._info, THREAD_DOMAIN)
            _, old_val = self._translator.translate_expr(expr, self._ctx)
            func_val = self.viper.EqCmp(old_func, old_val, self._position, self._info)
            old_info = self.viper.And(old_info, func_val, self._position, self._info)
        return old_info

    def _set_parameter_aliases(self, method: PythonMethod) -> List[Stmt]:
        """
        Sets var aliases in the context so that references to the parameters of this
        method are translated to references to the respective getArg calls instead.
        """
        arg_vars = []
        stmts = []
        for index, arg in enumerate(method._args.values()):
            arg_var = self._ctx.actual_function.create_variable(
                'thread_arg', arg.type, self._translator.translator)
            arg_vars.append(arg_var)
            index_lit = self.viper.IntLit(index, self._position, self._info)
            arg_expr = self.viper.DomainFuncApp(GET_ARG_FUNC,
                                                [self._thread, index_lit],
                                                self.viper.Ref, self._position,
                                                self._info, THREAD_DOMAIN)
            stmts.append(self.viper.LocalVarAssign(arg_var.ref(),
                                                   arg_expr,
                                                   self._position, self._info))
            type_info = self._translator.type_check(arg_var.ref(),
                                                    arg.type, self._position,
                                                    self._ctx)
            stmts.append(self.viper.Inhale(type_info, self._position, self._info))
        for index, name in enumerate(method._args):
            self._ctx.set_alias(name, arg_vars[index])
        return stmts

    def _add_precondition_exhales(self) -> None:
        """
        Creates statements that conditionally exhale the preconditions of the possible
        thread targets, inhale join permissions, remember values of old expressions in
        method postconditions.
        """
        method_id_type = self.viper.DomainType(METHOD_ID_DOMAIN, {}, [])
        actual_method = self.viper.DomainFuncApp(GET_METHOD_FUNC, [self._thread],
                                                 method_id_type, self._position,
                                                 self._info, THREAD_DOMAIN)
        for method in self._targets:
            # Forked methods must not have obligations in their postconditions.
            for instances in method.obligation_info._postcondition_instances.values():
                if instances:
                    raise InvalidProgramException(self._target_node,
                                                  'invalid.thread.start')
            collector = OldExpressionCollector()
            for post, _ in method.postcondition:
                collector.visit(post)

            stmts = []

            # To prepare translating the thread precondition, create alias variables for
            # each parameter and assign the argument values.
            arg_stmts = self._set_parameter_aliases(method)
            stmts.extend(arg_stmts)

            self._ctx.inlined_calls.append(method)
            old_loop_stack = self._ctx.obligation_context._loop_stack
            self._ctx.obligation_context._loop_stack = []
            self._ctx.ignore_waitlevel_constraints = True

            # Remember values of old expressions in postcondition.
            old_info = self._remember_old_expressions(method, collector)
            stmts.append(self.viper.Inhale(old_info, self._position, self._info))

            # Translate the actual precondition.
            pre_assertion = self.viper.TrueLit(self._position, self._info)
            for pre, _ in method.precondition:
                _, pre_val = self._translator.translate_expr(pre, self._ctx, impure=True,
                                                             target_type=self.viper.Bool)
                pre_assertion = self.viper.And(pre_assertion, pre_val, self._position,
                                               self._info)
            stmts.append(self.viper.Exhale(pre_assertion.whenExhaling(), self._position,
                                           self._info))

            # Inhale join permission.
            joinable = self._create_join_permission(method)
            stmts.append(self.viper.Inhale(joinable, self._position, self._info))

            for name in method._args:
                self._ctx.remove_alias(name)
            self._ctx.inlined_calls.pop()
            self._ctx.obligation_context._loop_stack = old_loop_stack
            self._ctx.ignore_waitlevel_constraints = False

            # Do all this under the condition that the current method is the thread's
            # actual target method.
            this_method = self.viper.DomainFuncApp(method.threading_id, [],
                                                   method_id_type, self._position,
                                                   self._info, METHOD_ID_DOMAIN)
            method_cond = self.viper.EqCmp(actual_method, this_method, self._position,
                                           self._info)
            then_block = self._translator.translate_block(stmts, self._position,
                                                          self._info)
            else_block = self._translator.translate_block([], self._position, self._info)
            conditional = self.viper.If(method_cond, then_block, else_block,
                                        self._position, self._info)
            self._statements.append(conditional)

    def _add_waitlevel(self) -> None:
        level = self.create_level_call(sil.RefExpr(self._thread))
        comp = self._create_level_below(level, self._ctx)
        comp = comp.translate(self._translator, self._ctx, self._position, self._info)
        if not obligation_config.disable_waitlevel_check:
            self._statements.append(self.viper.Inhale(comp, self._position, self._info))

    def _create_level_below(
            self, expr: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        residue_level_var = sil.PermVar(ctx.actual_function.obligation_info.residue_level)
        obligation = self._obligation_manager.must_release_obligation
        fields = obligation.create_fields_untranslated()
        var = ctx.current_function.create_variable(
            '_r', ctx.module.global_module.classes[OBJECT_TYPE],
            self._translator.translator, local=False)
        op = operator.lt(self.create_level_call(sil.RefVar(var)), expr)
        for_perms = [sil.ForPerm(var.sil_name, f, op) for f in fields]
        return sil.BigAnd(for_perms + [operator.lt(residue_level_var, expr)])

    def _translate_level(self, node: ast.Call) -> sil.PermExpression:
        """Translate a call to ``Level``."""
        assert len(node.args) == 1
        arg = sil.RefVar(node.args[0])
        return self.create_level_call(arg)

    def create_level_call(self, expr: sil.RefExpression) -> sil.PermExpression:
        return sil.PermCall('Level', [sil.CallArg('r', sil.REF, expr)])

    def get_statements(self) -> List[Stmt]:
        return self._statements
