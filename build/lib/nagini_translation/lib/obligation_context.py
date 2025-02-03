"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Classes for storing obligation translation state."""


from typing import Optional


class ObligationContext:
    """Current state that is related to obligation translation."""

    def __init__(self) -> None:
        self._loop_stack = []

        self.is_translating_posts = False
        """Are we currently translating a postcondition?"""

    @property
    def current_loop_info(self) -> object:
        """Get info of the inner most loop.

        Method type is set to ``object`` to indicate that the result
        should be opaque to all code except obligation implementation.
        """
        assert self._loop_stack
        return self._loop_stack[-1]

    def get_surrounding_loop_info(self) -> Optional[object]:
        """Get info of the loop surrounding the inner most loop.

        Method type is set to ``object`` to indicate that the result
        should be opaque to all code except obligation implementation.
        """
        if len(self._loop_stack) >= 2:
            # Surrounding loop exists only if there are at least two
            # loops in the loop stack.
            return self._loop_stack[-2]
        else:
            return None

    def push_loop_info(self, info: object) -> None:
        """Push loop information to loop stack.

        This method should be called just before a new loop is being
        translated.
        """
        self._loop_stack.append(info)

    def pop_loop_info(self) -> None:
        """Pop loop information from loop stack.

        This method should be called just after a loop was translated.
        """
        self._loop_stack.pop()

    def is_translating_loop(self) -> bool:
        """Return if we currently translating a loop."""
        return bool(self._loop_stack)
