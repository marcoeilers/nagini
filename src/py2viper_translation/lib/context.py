from contextlib import contextmanager
from py2viper_translation.lib.constants import ERROR_NAME, RESULT_NAME
from py2viper_translation.lib.io_context import IOOpenContext
from py2viper_translation.lib.program_nodes import (
    PythonMethod,
    PythonVar,
    PythonVarBase,
)
from typing import Dict, List


class Context:
    """
    Contains the current state of the entire translation process.
    """

    def __init__(self) -> None:
        self.current_function = None
        self.current_class = None
        self.var_aliases = {}
        self.old_aliases = {}
        self.label_aliases = {}
        self.position = []
        self.info = None
        self.program = None
        self.inlined_calls = []
        self.ignore_family_folds = False
        self.added_handlers = []
        self.loop_iterators = {}
        self.io_open_context = IOOpenContext()
        self._alias_context_stack = []
        self._current_alias_context = []

    def get_all_vars(self) -> List[PythonVar]:
        res = []
        if self.current_function:
            res += list(self.current_function.locals.items())
            res += list(self.current_function.args.items())
        if self.program:
            res += list(self.program.global_vars.items())

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
        else:
            del self.var_aliases[name]

