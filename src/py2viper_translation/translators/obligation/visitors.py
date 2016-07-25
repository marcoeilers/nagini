"""Visitors for collecting information about obligation use."""


import ast

from typing import List

from py2viper_translation.lib.program_nodes import (
    PythonMethod,
)
from py2viper_translation.lib.guard_collectors import (
    GuardCollectingVisitor,
)
from py2viper_translation.translators.obligation.manager import (
    ObligationManager,
)
from py2viper_translation.translators.obligation.types.base import (
    ObligationInstance,
)


class GuardedObligationInstance:
    """Obligation instance with its guard."""

    def __init__(
            self, guard: List[ast.AST],
            obligation_instance: ObligationInstance) -> None:
        self.guard = guard
        self.obligation_instance = obligation_instance


class PythonMethodObligationInfo(GuardCollectingVisitor):
    """Info about the obligation use in a specific method."""

    def __init__(self, obligaton_manager: ObligationManager) -> None:
        super().__init__()
        self._obligation_manager = obligaton_manager
        self._precondition_instances = {}
        self._postcondition_instances = {}
        for obligation in self._obligation_manager.obligations:
            obligation_id = obligation.identifier()
            self._precondition_instances[obligation_id] = []
            self._postcondition_instances[obligation_id] = []
        self._current_instance_map = None

    def traverse_preconditions(self, method: PythonMethod) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._precondition_instances
        for precondition, aliases in method.precondition:
            self.traverse(precondition)
        self._current_instance_map = None

    def traverse_postconditions(self, method: PythonMethod) -> None:
        """Collect all needed information about obligations."""
        assert self._current_instance_map is None
        self._current_instance_map = self._postcondition_instances
        for postcondition, aliases in method.postcondition:
            self.traverse(postcondition)
        self._current_instance_map = None

    def visit_Call(self, node: ast.Call) -> None:
        for obligation in self._obligation_manager.obligations:
            obligation_instance = obligation.check_node(node)
            if obligation_instance:
                instance = GuardedObligationInstance(
                    self.current_guard[:], obligation_instance)
                self._current_instance_map[obligation.identifier()].append(
                    instance)
                break
        else:
            super().visit_Call(node)
