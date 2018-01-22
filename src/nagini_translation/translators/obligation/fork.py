import ast
import copy
import operator

from typing import List

from nagini_translation.lib import silver_nodes as sil
from nagini_translation.lib.constants import (
    JOINABLE_FUNC,
    THREAD_POST_PRED,
)
from nagini_translation.lib.context import Context
from nagini_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
    Stmt
)
from nagini_translation.lib.util import (
    InvalidProgramException,
    OldExpressionCollector,
    OldExpressionNormalizer,
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

    def _add_precondition_exhales(self) -> None:
        method_id_type = self.viper.DomainType("ThreadingID", {}, [])
        actual_method = self.viper.DomainFuncApp("getMethod", [self._thread],
                                                 method_id_type, self._position,
                                                 self._info, "Thread")
        for method in self._targets:
            for instances in method.obligation_info._postcondition_instances.values():
                if instances:
                    raise InvalidProgramException(self._target_node,
                                                  'invalid.thread.start')
            collector = OldExpressionCollector()
            for post, _ in method.postcondition:
                collector.visit(post)

            stmts = []
            arg_vars = []
            for index, arg in enumerate(method._args.values()):
                arg_var = self._ctx.actual_function.create_variable(
                    'thread_arg', arg.type, self._translator.translator)
                arg_vars.append(arg_var)
                index_lit = self.viper.IntLit(index, self._position, self._info)
                arg_expr = self.viper.DomainFuncApp("getArg", [self._thread, index_lit],
                                                    self.viper.Ref, self._position,
                                                    self._info, "Thread")
                stmts.append(self.viper.LocalVarAssign(arg_var.ref(),
                                                       arg_expr,
                                                       self._position, self._info))
                type_info = self._translator.type_check(arg_var.ref(),
                                                        arg.type, self._position,
                                                        self._ctx)
                stmts.append(self.viper.Inhale(type_info, self._position, self._info))
            for index, name in enumerate(method._args):
                self._ctx.set_alias(name, arg_vars[index])
            # old_class = self._ctx.current_class
            self._ctx.inlined_calls.append(method)

            old_info = self.viper.TrueLit(self._position, self._info)
            normalizer = OldExpressionNormalizer()
            normalizer.arg_names = [arg for arg in method._args]
            for expr in collector.expressions:
                print_expr = normalizer.visit(copy.deepcopy(expr))
                name = pprint(print_expr)
                id = self.viper.IntLit(self._translator._get_string_value(name),
                                       self._position, self._info)
                old_func = self.viper.DomainFuncApp('getOld', [self._thread, id],
                                                    self.viper.Ref, self._position,
                                                    self._info," Thread")
                _, old_val = self._translator.translate_expr(expr, self._ctx)
                func_val = self.viper.EqCmp(old_func, old_val, self._position, self._info)
                old_info = self.viper.And(old_info, func_val, self._position, self._info)
            stmts.append(self.viper.Inhale(old_info, self._position, self._info))

            pre_assertion = self.viper.TrueLit(self._position, self._info)
            for pre, _ in method.precondition:
                _, pre_val = self._translator.translate_expr(pre, self._ctx, impure=True)
                pre_assertion = self.viper.And(pre_assertion, pre_val, self._position,
                                               self._info)
            stmts.append(self.viper.Exhale(pre_assertion.whenExhaling(), self._position,
                                           self._info))
            tcond = method.obligation_info.create_termination_check(True)
            tcond = tcond.translate(self._translator, self._ctx, self._position,
                                    self._info)
            for name in method._args:
                self._ctx.remove_alias(name)
            self._ctx.inlined_calls.pop()
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
            stmts.append(self.viper.Inhale(joinable, self._position, self._info))

            this_method = self.viper.DomainFuncApp(method.threading_id, [], method_id_type, self._position, self._info,
                                                   "ThreadingID")
            method_cond = self.viper.EqCmp(actual_method, this_method, self._position, self._info)
            then_block = self._translator.translate_block(stmts, self._position, self._info)
            else_block = self._translator.translate_block([], self._position, self._info)
            conditional = self.viper.If(method_cond, then_block, else_block,
                                        self._position, self._info)
            self._statements.append(conditional)

    def _add_waitlevel(self) -> None:
        level = self.create_level_call(sil.RefExpr(self._thread))
        comp = self._create_level_below(level, self._ctx)
        comp = comp.translate(self._translator, self._ctx, self._position, self._info)
        self._statements.append(self.viper.Inhale(comp, self._position, self._info))

    def _create_level_below(
            self, expr: sil.PermExpression,
            ctx: Context) -> sil.BoolExpression:
        residue_level_var = sil.PermVar(ctx.actual_function.obligation_info.residue_level)
        obligation = self._obligation_manager.must_release_obligation
        fields = obligation.create_fields_untranslated()
        var = ctx.current_function.create_variable(
            '_r', ctx.module.global_module.classes['object'],
            self._translator.translator, local=False)
        for_perm = sil.ForPerm(
            var.sil_name,
            fields,
            operator.lt(self.create_level_call(sil.RefVar(var)), expr))
        return sil.BigAnd([for_perm, operator.lt(residue_level_var, expr)])

    def _translate_level(self, node: ast.Call) -> sil.PermExpression:
        """Translate a call to ``Level``."""
        assert len(node.args) == 1
        arg = sil.RefVar(node.args[0])
        return self.create_level_call(arg)

    def create_level_call(self, expr: sil.RefExpression) -> sil.PermExpression:
        return sil.PermCall('Level', [sil.CallArg('r', sil.REF, expr)])

    def _add_inhale_joinable(self) -> None:
        tcond = self._obligation_info.create_termination_check(False)

    def get_statements(self) -> List[Stmt]:
        return self._statements

