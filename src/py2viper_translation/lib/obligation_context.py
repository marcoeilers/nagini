"""Classes for storing obligation translation state."""


import ast

from typing import List, Union

from py2viper_translation.lib.program_nodes import (
    PythonVar,
)


class LoopInfo:
    """Information about loop."""

    def __init__(
            self, node: Union[ast.While, ast.For],
            invariants: List[ast.expr], measure_map: 'MeasureMap',
            loop_check_before: PythonVar) -> None:
        self.node = node
        self.invariants = invariants
        self.measure_map = measure_map
        self.loop_check_before = loop_check_before


class ObligationContext:
    """Current state that is related to obligation translation."""

    def __init__(self) -> None:
        self._loop_stack = []

        self.is_translating_posts = False
        """Are we currently translating a postcondition?"""

    @property
    def _current_loop_info(self) -> LoopInfo:
        """Get info of the inner most loop."""
        assert self._loop_stack
        return self._loop_stack[-1]

    def push_loop_info(
            self, node: Union[ast.While, ast.For],
            invariants: List[ast.expr], measure_map: 'MeasureMap',
            loop_check_before: PythonVar) -> None:
        """Push loop information to loop stack.

        This method should be called just before a new loop is being
        translated.
        """
        info = LoopInfo(node, invariants, measure_map, loop_check_before)
        self._loop_stack.append(info)

    def pop_loop_info(self) -> None:
        """Pop loop information from loop stack.

        This method should be called just after a loop was translated.
        """
        self._loop_stack.pop()

    def is_translating_loop(self) -> bool:
        """Return if we currently translating a loop."""
        return bool(self._loop_stack)

    def get_current_loop_check_before(self) -> PythonVar:
        """Get loop check of the inner most loop."""
        return self._current_loop_info.loop_check_before

    def get_current_measure_map(self) -> PythonVar:
        """Get measure map of the inner most loop."""
        return self._current_loop_info.measure_map

    def get_current_invariants(self) -> List[ast.expr]:
        """Get invariants of the inner most loop."""
        return self._current_loop_info.invariants
