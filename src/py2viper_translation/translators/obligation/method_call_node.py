"""Code for constructing Silver Method call node with obligation stuff."""


import ast

from typing import List, Optional, Union

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.context import Context
from py2viper_translation.lib.errors import Rules, rules
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonIOExistentialVar,
    PythonVar,
)
from py2viper_translation.lib.typedefs import (
    Info,
    Position,
    Stmt,
)
from py2viper_translation.lib.util import (
    pprint,
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
        self.original_args = args[:]
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
        if not self._is_target_axiomatized():
            self._check_measures_are_positive()
        self._save_must_terminate_amount(
            self._obligation_info.original_must_terminate_var)
        self._inhale_additional_must_terminate()
        self._save_must_terminate_amount(
            self._obligation_info.increased_must_terminate_var)
        self._add_call()
        self._check_must_terminate()
        self._reset_must_terminate()

    def _add_aditional_arguments(self) -> None:
        """Add current thread and caller measure map arguments."""
        args = [
            self._obligation_info.current_thread_var.ref(
                self._node, self._ctx),
            self._obligation_info.method_measure_map.get_var().ref(
                self._node, self._ctx),
        ]
        self._obligation_method_call.prepend_args(args)

    def _check_measures_are_positive(self) -> None:
        """Check that callee measures are positive."""
        instances = self._obligation_info.get_all_precondition_instances()
        with self._ctx.aliases_context():
            self._set_up_method_arg_aliases()
            for instance in instances:

                guard_expression = instance.create_guard_expression()
                check = expr.Implies(
                    guard_expression,
                    instance.obligation_instance.get_measure() > 0)
                assertion = expr.Assert(check)

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

    def _save_must_terminate_amount(
            self, amount_var: PythonVar) -> None:
        """Save the original permission amount to a variable."""
        predicate = self._get_must_terminate_predicate()
        assign = expr.Assign(amount_var, expr.CurrentPerm(predicate))
        info = self._to_info('Save current MustTerminate amount.')
        self._append_statement(assign, info=info)

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
        info = self._to_info('Inhale additional MustTerminate amount.')
        self._append_statement(inhale, info=info)

    def _add_call(self) -> None:
        """Add the actual code node."""
        call = self._obligation_method_call
        statement = self._viper.MethodCall(
            call.name, call.args, call.targets,
            self._position, self._info)
        self._statements.append(statement)

    def _check_must_terminate(self) -> None:
        """Check if callee picked MustTerminate obligation."""
        original_amount = self._obligation_info.original_must_terminate_var
        increased_amount = self._obligation_info.increased_must_terminate_var
        predicate = self._get_must_terminate_predicate()
        check = expr.Implies(
            expr.NoPerm() < expr.VarRef(original_amount),
            expr.CurrentPerm(predicate) < expr.VarRef(increased_amount))
        assertion = expr.Assert(check)
        position = self._to_position(
            conversion_rules=rules.OBLIGATION_MUST_TERMINATE_NOT_TAKEN)
        info = self._to_info('Check that callee took MustTerminate.')
        self._append_statement(assertion, position, info)

    def _reset_must_terminate(self) -> None:
        """Reset ``MustTerminate`` permission to its original level.

        .. note::

            Implication is needed because in Silicon if callee took all
            permission, the ``exhale acc(..., none)`` would fail, even
            though this exhale does nothing.
        """
        predicate = self._get_must_terminate_predicate()
        original_amount = expr.VarRef(
            self._obligation_info.original_must_terminate_var)
        perm = expr.CurrentPerm(predicate) - original_amount
        exhale = expr.Exhale(expr.Implies(
            expr.CurrentPerm(predicate) > expr.NoPerm(),
            expr.Acc(predicate, perm)))
        info = self._to_info('Reset MustTerminate amount to original level.')
        self._append_statement(exhale, info=info)

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

    def _to_position(
            self, node: ast.AST = None,
            conversion_rules: Rules = None,
            error_node: Union[str, ast.AST] = None) -> Position:
        error_string = None
        if error_node is not None:
            if isinstance(error_node, ast.AST):
                error_string = pprint(error_node)
            else:
                error_string = error_node
        return self._translator.to_position(
            node or self._node, self._ctx, error_string=error_string,
            rules=conversion_rules)

    def _to_info(self, template, *args, **kwargs) -> Info:
        return self._translator.to_info(
            [template.format(*args, **kwargs)], self._ctx)

    def _set_up_method_arg_aliases(self) -> None:
        """Set up aliases from parameters to arguments."""
        if self._node is None:
            # self._node is None only when we do behavioural subtyping
            # check. In this case, all arguments are the same and we do
            # not need to set up aliases.
            return
        triples = zip(
            self._method.args.values(),
            self._node.args,
            self._obligation_method_call.original_args)
        # TODO: Refactor: This loop is identical to
        # set_up_io_operation_input_aliases.
        for parameter, py_arg, sil_arg in triples:
            var_type = self._translator.get_type(py_arg, self._ctx)
            var = PythonIOExistentialVar(parameter.name, py_arg, var_type)
            var.set_ref(sil_arg)
            self._ctx.set_alias(parameter.name, var)

    def _append_statement(
            self, statement: expr.Statement,
            position: Position = None, info: Info = None) -> None:
        translated = statement.translate(
            self._translator, self._ctx,
            position or self._position,
            info or self._info)
        self._statements.append(translated)

    def _is_target_axiomatized(self) -> bool:
        """Check if target is axiomatic method."""
        return self._method.interface
