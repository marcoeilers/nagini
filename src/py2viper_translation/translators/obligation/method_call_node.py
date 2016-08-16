"""Code for constructing Silver Method call node with obligation stuff."""


import ast

from typing import List, Optional

from py2viper_translation.lib import silver_nodes as sil
from py2viper_translation.lib.config import obligation_config
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import rules
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonIOExistentialVar,
)
from py2viper_translation.lib.typedefs import (
    Expr,
    Info,
    Position,
)
from py2viper_translation.lib.util import (
    InvalidProgramException,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.node_constructor import (
    StatementNodeConstructorBase,
)
from py2viper_translation.translators.obligation.obligation_info import (
    PythonMethodObligationInfo,
)
from py2viper_translation.translators.obligation.types.must_terminate import (
    TerminationGuarantee,
)


class ObligationMethodCall:
    """Info for generating Silver ``MethodCall`` AST node."""

    def __init__(
            self, name: str, args: List[Expr], targets: List[Expr]) -> None:
        self.name = name
        self.original_args = args[:]
        self.args = args
        self.targets = targets

    def prepend_arg(self, arg: Expr) -> None:
        """Prepend ``args`` to the argument list."""
        self.args.insert(0, arg)


class ObligationMethodCallNodeConstructor(StatementNodeConstructorBase):
    """A class that creates a method call node with obligation stuff."""

    def __init__(
            self, obligation_method_call: ObligationMethodCall,
            position: Position, info: Info,
            translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager,
            target_method: Optional[PythonMethod],
            target_node: Optional[ast.AST]) -> None:
        """Constructor.

        If ``target_node`` is ``None``, then:

        1.  It is assumed that we are translating a behavioural
            subtyping check.
        2.  ``target_method.node`` is used for computing default
            position.
        """
        super().__init__(
            translator, ctx, obligation_manager, position, info,
            target_node or target_method.node)
        self._obligation_method_call = obligation_method_call
        self._target_method = target_method
        self._target_node = target_node

    def construct_call(self) -> None:
        """Construct statements to perform a call."""
        self._check_valid_call()
        self._add_aditional_arguments()
        if not self._is_axiomatized_target():
            self._check_measures_are_positive()
        if not self._check_skip_normal_termination_checks():
            self._save_must_terminate_amount(
                self._obligation_info.original_must_terminate_var)
            self._inhale_additional_must_terminate()
            self._save_must_terminate_amount(
                self._obligation_info.increased_must_terminate_var)
        elif self._check_no_forced_termination_needed():
            self._check_no_forced_termination()
        self._add_call()
        if not self._check_skip_normal_termination_checks():
            self._check_must_terminate()
            self._reset_must_terminate(
                self._obligation_info.original_must_terminate_var)

    def _get_context_termination(self) -> TerminationGuarantee:
        if self._ctx.obligation_context.is_translating_loop():
            obligation_info = self._ctx.obligation_context.current_loop_info
        else:
            obligation_info = self._ctx.actual_function.obligation_info
        return obligation_info.get_termination_guarantee()

    def _get_target_termination(self) -> TerminationGuarantee:
        obligation_info = self._target_method.obligation_info
        return obligation_info.get_termination_guarantee()

    def _check_skip_normal_termination_checks(self) -> bool:
        """Check if we can skip termination checks."""
        return (self._get_target_termination() is not
                TerminationGuarantee.may_terminating)

    def _check_no_forced_termination_needed(self) -> bool:
        """Check if we need to guarantee not-having termination obligation."""
        return (self._get_context_termination() is
                TerminationGuarantee.may_terminating and
                self._get_target_termination() is
                TerminationGuarantee.potentially_non_terminating)

    def _check_valid_call(self) -> None:
        """Check that terminating context does not call non-terminating."""
        if (self._get_context_termination() is
                TerminationGuarantee.always_terminating):
            if (self._get_target_termination() is
                    TerminationGuarantee.potentially_non_terminating):
                raise InvalidProgramException(
                    self._target_node,
                    'non_terminating_call_in_terminating_context')

    def _check_no_forced_termination(self) -> None:
        """Check that termination is not required.

        Check that ``may_terminating`` does not require
        ``potentially_non_terminating`` to terminate.
        """
        if obligation_config.disable_termination_check:
            return
        predicate = self._get_must_terminate_predicate()
        assertion = sil.Assert(sil.CurrentPerm(predicate) == sil.NoPerm())
        position = self._to_position(
            conversion_rules=rules.OBLIGATION_MUST_TERMINATE_NOT_TAKEN)
        info = self._to_info(
            'Check that callee is not required to terminate.')
        self._append_statement(assertion, position, info)

    def _add_aditional_arguments(self) -> None:
        """Add current thread and caller measure map arguments."""
        if not obligation_config.disable_measures:
            self._obligation_method_call.prepend_arg(
                self._obligation_info.method_measure_map.get_var().ref(
                    self._target_node, self._ctx))
        self._obligation_method_call.prepend_arg(
            self._obligation_info.current_thread_var.ref(
                self._target_node, self._ctx))

    def _check_measures_are_positive(self) -> None:
        """Check that callee measures are positive."""
        if obligation_config.disable_measures:
            return
        target_info = self._target_obligation_info
        instances = target_info.get_all_precondition_instances()
        with self._ctx.aliases_context():
            self._set_up_method_arg_aliases()
            for instance in instances:
                if instance.obligation_instance.is_fresh():
                    continue

                guard_expression = instance.create_guard_expression()
                check = sil.Implies(
                    guard_expression,
                    instance.obligation_instance.get_measure() > 0)
                if check.is_always_true():
                    continue
                assertion = sil.Assert(check)

                obligation_node = instance.obligation_instance.node
                measure_position = self._to_position(obligation_node)
                self._ctx.position.append(('call target', measure_position))
                call_position = self._to_position(
                    conversion_rules=rules.OBLIGATION_MEASURE_NON_POSITIVE,
                    error_node=obligation_node)
                info = self._to_info(
                    'Positive measure check for {} at ({}:{})',
                    instance.obligation_instance.obligation.identifier(),
                    obligation_node.lineno, obligation_node.col_offset)
                self._append_statement(assertion, call_position, info)
                self._ctx.position.pop()

    def _inhale_additional_must_terminate(self) -> None:
        """Inhale additional permission to ``MustTerminate``.

        This is needed to prevent the call from failing because of
        missing permission to ``MustTerminate``. For example, this can
        happen when non-terminating method calls a terminating one.
        """
        if obligation_config.disable_termination_check:
            return
        predicate = self._get_must_terminate_predicate()

        # Check that we have an expected amount of MustTerminate
        # permission.
        # This assert is for testing purposes only. It can be removed as
        # soon as we are sure that obligation encoding works.
        assertion = sil.Assert(sil.BigOr([
            sil.CurrentPerm(predicate) == sil.NoPerm(),
            sil.CurrentPerm(predicate) == sil.FullPerm(),
        ]))
        info = self._to_info(
            'Check that we have expected amount of MustTerminate.')
        self._append_statement(assertion, info=info)

        # Inhale additional MustTerminate permission so that we have the
        # amount mentioned in the precondition + 1.
        if self._is_axiomatized_target():
            count = sil.RawIntExpression(1)
        else:
            instances = self._target_obligation_info.get_precondition_instances(
                self._must_terminate.identifier())
            count = sil.RawIntExpression(len(instances))
        inc_count = sil.CondInc(
            sil.CurrentPerm(predicate) == sil.NoPerm(), count)
        inhale = sil.Inhale(sil.Acc(predicate, sil.IntegerPerm(inc_count)))
        info = self._to_info('Inhale additional MustTerminate amount.')
        self._append_statement(inhale, info=info)

    def _add_call(self) -> None:
        """Add the actual call node."""
        call = self._obligation_method_call
        statement = self._viper.MethodCall(
            call.name, call.args, call.targets,
            self._position, self._info)
        self._statements.append(statement)

    def _check_must_terminate(self) -> None:
        """Check if callee picked MustTerminate obligation."""
        if obligation_config.disable_termination_check:
            return
        original_amount = self._obligation_info.original_must_terminate_var
        increased_amount = self._obligation_info.increased_must_terminate_var
        predicate = self._get_must_terminate_predicate()
        check = sil.Implies(
            sil.NoPerm() < sil.VarRef(original_amount),
            sil.CurrentPerm(predicate) < sil.VarRef(increased_amount))
        assertion = sil.Assert(check)
        position = self._to_position(
            conversion_rules=rules.OBLIGATION_MUST_TERMINATE_NOT_TAKEN)
        info = self._to_info('Check that callee took MustTerminate.')
        self._append_statement(assertion, position, info)

    def _is_axiomatized_target(self) -> bool:
        """Check if call target is an axiomatic method."""
        return self._target_method is None or self._target_method.interface

    @property
    def _target_obligation_info(self) -> PythonMethodObligationInfo:
        return self._target_method.obligation_info

    def _set_up_method_arg_aliases(self) -> None:
        """Set up aliases from parameters to arguments."""
        if self._target_node is None:
            # self._target_node is None only when we do behavioural subtyping
            # check. In this case, all arguments are the same and we do
            # not need to set up aliases.
            return
        parameters = list(self._target_method.args.values())
        if self._target_method.var_arg:
            parameters.append(self._target_method.var_arg)
        if self._target_method.kw_arg:
            parameters.append(self._target_method.kw_arg)
        args = self._obligation_method_call.original_args
        if 2 * len(parameters) + 1 == len(args):
            # TODO: Find out a proper way to check if we are running
            # under SIF.
            args = args[0:-1:2]
        assert len(parameters) == len(args)
        # TODO: Refactor: This loop is identical to
        # set_up_io_operation_input_aliases.
        for parameter, sil_arg in zip(parameters, args):
            var = PythonIOExistentialVar(parameter.name, None, parameter.type)
            var.set_ref(sil_arg)
            self._ctx.set_alias(parameter.name, var)
