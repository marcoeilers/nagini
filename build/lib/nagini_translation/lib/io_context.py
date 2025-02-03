"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Classes for storing IO translation state."""


from collections import OrderedDict
from typing import List, Tuple

from nagini_translation.lib.program_nodes import PythonVar
from nagini_translation.lib.typedefs import Expr


class IOOpenContext:
    """Current state of IO operation open translation process."""

    def __init__(self) -> None:

        self._is_opening = False
        """Are we currently translating IO open?"""

        self._open_var_aliases = {}  # type: Dict[str, PythonVar]
        """Variables used while opening IO operation."""

        self._open_var_alias_definitions = OrderedDict()
        """Initial assignments to variables used in opening IO operation."""

    def start_io_operation_open(self) -> None:
        """Check state before IO operation open.

        This method is supposed to be called just before starting to
        translate IO operation open. It checks if context is in a good
        state.
        """
        assert not self._is_opening
        assert not self._open_var_aliases
        assert not self._open_var_alias_definitions
        self._is_opening = True

    def stop_io_operation_open(self) -> None:
        """Clean state after IO operation open.

        This method is supposed to be called just after finishing to
        translate IO operation open. It cleans up the context state.
        """
        assert self._is_opening
        self._is_opening = False
        self._open_var_aliases.clear()
        self._open_var_alias_definitions.clear()

    def add_variable(self, var_name: str, var: PythonVar) -> None:
        """Add IO opening variable."""
        assert self._is_opening
        self._open_var_aliases[var_name] = var

    def contains_variable(self, var_name: str) -> bool:
        """Check if variable is from IO opening."""
        return self._is_opening and var_name in self._open_var_aliases

    def get_variable(self, var_name) -> PythonVar:
        """Get variable that is used while opening IO operation."""
        assert self._is_opening
        return self._open_var_aliases[var_name]

    def is_variable_defined(self, var_name: str) -> bool:
        """Check if variable has already a definition."""
        assert self._is_opening
        return var_name in self._open_var_alias_definitions

    def define_variable(self, var_name: str, definition: Expr) -> None:
        """Assign definition to a variable."""
        assert self._is_opening
        self._open_var_alias_definitions[var_name] = definition

    def get_ordered_variable_defs(
            self) -> List[Tuple[PythonVar, Expr]]:
        """Get variables with their definitions.

        Returned variables are in their definition order.
        """
        assert self._is_opening
        result = []
        for name, definition in self._open_var_alias_definitions.items():
            result.append((self._open_var_aliases[name], definition))
        return result
