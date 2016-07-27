"""Visitors for collecting information about obligation use."""


import ast

from typing import List

from py2viper_translation.lib import expressions as expr
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonProgram,
    PythonVar,
)
from py2viper_translation.lib.guard_collectors import (
    GuardCollectingVisitor,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.measures import (
    MeasureMap,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
)


CURRENT_THREAD_NAME = '_cthread'
MEASURES_CALLER_NAME = '_caller_measures'
MEASURES_METHOD_NAME = '_method_measures'


class GuardedObligationInstance:
    """Obligation instance with its guard."""

    def __init__(
            self, guard: List[ast.AST],
            obligation_instance: ObligationInstance) -> None:
        self.guard = guard
        self.obligation_instance = obligation_instance

    def create_guard_expression(self) -> expr.BigAnd:
        """Create a conjunction representing a guard."""
        conjunction = expr.BigAnd([
            expr.PythonBoolExpression(part)
            for part in self.guard
        ])
        return conjunction


class PythonMethodObligationInfo(GuardCollectingVisitor):
    """Info about the obligation use in a specific method."""

    def __init__(
            self, obligaton_manager: ObligationManager,
            method: PythonMethod, translator: 'Translator') -> None:
        super().__init__()
        self._obligation_manager = obligaton_manager
        self._all_instances = {}
        self._precondition_instances = {}
        self._postcondition_instances = {}
        for obligation in self._obligation_manager.obligations:
            obligation_id = obligation.identifier()
            self._precondition_instances[obligation_id] = []
            self._postcondition_instances[obligation_id] = []
        self._current_instance_map = None
        self._method = method
        self.current_thread_var = self._create_var(
            CURRENT_THREAD_NAME, 'Thread', translator)
        caller_measure_map_var = self._create_var(
            MEASURES_CALLER_NAME, 'object', translator)
        self.caller_measure_map = MeasureMap(caller_measure_map_var)
        method_measure_map_var = self._create_var(
            MEASURES_METHOD_NAME, 'object', translator)
        self.method_measure_map = MeasureMap(method_measure_map_var)

    def traverse_preconditions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._precondition_instances
        for precondition, aliases in self._method.precondition:
            self.traverse(precondition)
        self._current_instance_map = None

    def traverse_postconditions(self) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._postcondition_instances
        for postcondition, aliases in self._method.postcondition:
            self.traverse(postcondition)
        self._current_instance_map = None

    def get_all_precondition_instances(self) -> None:
        """Return all precondition instances."""
        all_instances = []
        for instances in self._precondition_instances.values():
            all_instances.extend(instances)
        return all_instances

    def visit_Call(self, node: ast.Call) -> None:
        for obligation in self._obligation_manager.obligations:
            obligation_instance = obligation.check_node(
                node, self, self._method)
            if obligation_instance:
                instance = GuardedObligationInstance(
                    self.current_guard[:], obligation_instance)
                self._current_instance_map[obligation.identifier()].append(
                    instance)
                self._all_instances[node] = instance
                break
        else:
            super().visit_Call(node)

    def get_instance(self, node: ast.Call) -> GuardedObligationInstance:
        """Get ``GuardedObligationInstance`` represented by node."""
        return self._all_instances[node]

    def _get_program(self) -> PythonProgram:
        scope = self._method
        while scope.superscope:
            scope = scope.superscope
        return scope

    def _create_var(
            self, name: str, class_name: str,
            translator: 'Translator') -> PythonVar:
        program = self._get_program()
        cls = program.classes[class_name]
        return self._method.create_variable(
            name, cls, translator, local=False)
