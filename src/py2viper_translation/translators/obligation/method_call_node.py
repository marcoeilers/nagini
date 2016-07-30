"""Code for constructing Silver Method call node with obligation stuff."""


import ast

from typing import List, Optional

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Stmt,
)
from py2viper_translation.lib.viper_ast import ViperAST
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.types import must_terminate
from py2viper_translation.translators.obligation.visitors import (
    PythonMethodObligationInfo,
)


class ObligationMethodCall:
    """Info for generating Silver ``MethodCall`` AST node."""

    def __init__(self, name, args, targets) -> None:
        self.name = name
        self.args = args
        self.targets = targets

    def prepend_args(self, args) -> None:
        """Prepend ``args`` to the argument list."""
        self.args = args + self.args


class ObligationsMethodCallNodeConstructor:
    """A class that creates a method call node with obligation stuff."""

    def __init__(
            self, obligation_method_call: ObligationMethodCall,
            position, info,
            translator: 'AbstractTranslator', ctx: Context,
            obligation_manager: ObligationManager,
            target_method: Optional[PythonMethod],
            target_node: Optional[ast.AST]) -> None:
        self._obligation_method_call = obligation_method_call
        self._position = position
        self._info = info
        self._translator = translator
        self._ctx = ctx
        self._obligation_manager = obligation_manager
        self._method = target_method
        self._node = target_node
        self._statements = []

    def get_statements(self) -> List[Stmt]:
        """Get all generated statements."""
        return self._statements

    def construct_call(self) -> None:
        """Construct statements to perform a call."""
        self._add_aditional_arguments()
        # self._check_measures_are_positive()
        self._save_must_terminate_amount(
            self._obligation_info.original_must_terminate_var)
        self._inhale_additional_must_terminate()
        self._save_must_terminate_amount(
            self._obligation_info.increased_must_terminate_var)
        self._add_call()
        # self._check_must_terminate()
        self._reset_must_terminate()
        # TODO: Finish implementation.

    def _add_aditional_arguments(self) -> None:
        """Add current thread and caller measure map arguments."""
        args = [
            self._obligation_info.current_thread_var.ref(
                self._node, self._ctx),
            self._obligation_info.method_measure_map.get_var().ref(
                self._node, self._ctx),
        ]
        self._obligation_method_call.prepend_args(args)

    def _save_must_terminate_amount(
            self, amount_var: PythonVar) -> None:
        """Save the original permission amount to a variable."""
        predicate = self._get_must_terminate_predicate()
        assign = expr.Assign(amount_var, expr.CurrentPerm(predicate))
        self._append_statement(assign)

    def _inhale_additional_must_terminate(self) -> None:
        """Inhale additional permission to ``MustTerminate``.

        This is needed to prevent the call from failing because of
        missing permission to ``MustTerminate``. For example, this can
        happen when non-terminating method calls a terminating one.
        """
        if self._is_axiomatized_target():
            count = expr.RawIntExpression(1)
        else:
            instances = self._obligation_info.get_precondition_instances(
                self._must_terminate.identifier())
            count = expr.RawIntExpression(len(instances))
        predicate = self._get_must_terminate_predicate()
        inhale = expr.Inhale(expr.Acc(predicate, expr.IntegerPerm(count)))
        self._append_statement(inhale)

    def _add_call(self) -> None:
        """Add the actual code node."""
        call = self._obligation_method_call
        statement = self._viper.MethodCall(
            call.name, call.args, call.targets,
            self._position, self._info)
        self._statements.append(statement)

    def _reset_must_terminate(self) -> None:
        """Reset ``MustTerminate`` permission to its original level."""
        predicate = self._get_must_terminate_predicate()
        original_amount = expr.VarRef(
            self._obligation_info.original_must_terminate_var)
        perm = expr.CurrentPerm(predicate) - original_amount
        exhale = expr.Exhale(expr.Acc(predicate, perm))
        self._append_statement(exhale)

    def _is_axiomatized_target(self) -> bool:
        """Check if call target is an axiomatic method."""
        return self._method is None or self._method.interface

    @property
    def _obligation_info(self) -> PythonMethodObligationInfo:
        return self._method.obligation_info

    @property
    def _viper(self) -> ViperAST:
        return self._translator.viper

    @property
    def _must_terminate(self) -> must_terminate.MustTerminateObligation:
        return self._obligation_manager.must_terminate_obligation

    def _get_must_terminate_predicate(self) -> expr.Predicate:
        cthread = self._obligation_info.current_thread_var
        return self._must_terminate.create_predicate_access(cthread)

    def _append_statement(self, statement: expr.Statement) -> None:
        translated = statement.translate(
            self._translator, self._ctx, self._position, self._info)
        self._statements.append(translated)
