"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from contextlib import contextmanager
from nagini_translation.lib.constants import ERROR_NAME, RESULT_NAME
from nagini_translation.lib.io_context import IOOpenContext
from nagini_translation.lib.obligation_context import ObligationContext
from nagini_translation.lib.program_nodes import (
    PythonMethod,
    PythonType,
    PythonVar,
    PythonVarBase,
)
from nagini_translation.lib.typedefs import Expr
from typing import Dict, List


class Context:
    """
    Contains the current state of the entire translation process.
    """

    def __init__(self) -> None:
        self.current_function = None
        self.current_class = None
        self.current_contract_exception = None
        self.var_aliases = {}
        self.old_aliases = {}
        self.label_aliases = {}
        self.position = []
        self.info = None
        self.module = None
        self.inlined_calls = []
        self.ignore_family_folds = False
        self.added_handlers = []
        self.loop_iterators = {}
        self.io_open_context = IOOpenContext()
        self.obligation_context = ObligationContext()
        self._alias_context_stack = []
        self._current_alias_context = []
        self.bound_type_vars = {}
        self._global_counter = 0
        self.perm_factor = None     # If this is set, all translated permission amounts
                                    # are multiplied by this factor.
        self._old_aliases = {}      # Keys are pretty-printed Python expressions,
                                    # values are Silver expressions they should be
                                    # translated to.
        self.ignore_waitlevel_constraints = False      # If this is set, all encountered
                                                       # WaitLevel() < e constraints will
                                                       # be translated to true.
        # Whether Abstract Read Permissions may be used
        self.arp = False
        # Stores the thread object for which the contracts are currently translated.
        self.current_thread_object = None
        # True iff contracts for a thread start are translated.
        # Used to differentiate fresh token from old token permission.
        self.is_thread_start = False
        self.are_function_constants_used = False
        self.are_threading_constants_used = False
        self.sif = False
        self.allow_statements = False

    def get_fresh_int(self) -> int:
        """
        Returns a fresh integer value, to be used as a globally used counter
        where needed. Current use case is as an argument to constructors for
        various data types, to make the instances unique.
        """
        result = self._global_counter
        self._global_counter += 1
        return result

    @property
    def all_vars(self) -> List[PythonVar]:
        """
        Returns all variables accessible in the current context, i.e., global
        variables as well as local variables and arguments of the current
        function, if any.
        """
        res = []
        if self.current_function:
            res += list(self.current_function.locals.items())
            res += list(self.current_function.args.items())
        if self.module:
            res += list(self.module.global_vars.items())
        return res

    @property
    def actual_function(self) -> PythonMethod:
        """
        Returns the function/method which is actually currently being
        translated, i.e. if a function is currently being inlined, that
        function and not the one it is being inlined into.
        """
        if not self.inlined_calls:
            return self.current_function
        return self.inlined_calls[-1]

    @property
    def result_var(self) -> PythonVar:
        """
        Returns the result var of the current function or the current alias for
        it.
        """
        if RESULT_NAME in self.var_aliases:
            return self.var_aliases[RESULT_NAME]
        if self.current_function.result:
            return self.current_function.result
        return None

    @property
    def error_var(self) -> PythonVar:
        """
        Returns the error var of the current function or the current alias for
        it.
        """
        if ERROR_NAME in self.var_aliases:
            return self.var_aliases[ERROR_NAME]
        return self.current_function.error_var

    def get_label_name(self, name: str) -> str:
        """
        Returns the actual name of the given label in the current context, i.e.,
        looks for aliases.
        """
        if name in self.label_aliases:
            return self.label_aliases[name]
        return name

    @contextmanager
    def additional_aliases(self, aliases: Dict[str, PythonVarBase]) -> None:
        """
        Execute in a context with additional aliases.
        """
        for name, var in aliases.items():
            self.set_alias(name, var, None)
        try:
            yield
        finally:
            for name in aliases:
                self.remove_alias(name)

    @contextmanager
    def aliases_context(self) -> None:
        """
        All aliases added in this context are automatically removed at
        the end of it.
        """
        self._alias_context_stack.append(self._current_alias_context)
        self._current_alias_context = []
        try:
            yield
        finally:
            for name in self._current_alias_context:
                self.remove_alias(name)
            self._current_alias_context = self._alias_context_stack.pop()

    def set_alias(self, name: str, var: PythonVar,
                  replaces: PythonVar=None) -> None:
        """
        Sets an alias for a variable. Makes sure the alt_types of the alias
        variable match those of the variable it replaces. If there already is
        an alias for the given name, memorizes the old one and replaces it.
        """
        if name in self.var_aliases:
            if name not in self.old_aliases:
                self.old_aliases[name] = []
            self.old_aliases[name].append(self.var_aliases[name])
        if replaces:
            if replaces.alt_types:
                assert not var.alt_types
                var.alt_types = replaces.alt_types
        self.var_aliases[name] = var
        self._current_alias_context.append(name)

    def remove_alias(self, name: str) -> None:
        """
        Removes the alias for the given variable. If there was a different alias
        before, that one will be used again afterwards. Otherwise, there will
        no longer be an alias for this name.
        """
        if name in self.old_aliases and self.old_aliases[name]:
            old = self.old_aliases[name].pop()
            self.var_aliases[name] = old
        elif name in self.var_aliases:
            del self.var_aliases[name]

    def set_old_expr_alias(self, key: str, val: Expr) -> None:
        self._old_aliases[key] = val

    def clear_old_expr_aliases(self) -> None:
        self._old_aliases.clear()

    @property
    def old_expr_aliases(self):
        return self._old_aliases

    def get_contents(self, only_top: bool) -> Dict:
        """
        Returns the elements that can be accessed from this container (to be
        used by get_target). If 'only_top' is true, returns only top level
        elements that can be accessed without a receiver.
        """
        return self.var_aliases

