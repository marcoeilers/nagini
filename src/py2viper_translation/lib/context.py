from py2viper_translation.lib.constants import ERROR_NAME, RESULT_NAME
from py2viper_translation.lib.program_nodes import PythonMethod, PythonVar
from typing import List


class Context:
    """
    Contains the current state of the entire translation process.
    """

    def __init__(self) -> None:
        self.current_function = None
        self.current_class = None
        self.var_aliases = {}
        self.label_aliases = {}
        self.position = None
        self.info = None
        self.program = None
        self.inlined_calls = []
        self.ignore_family_folds = False
        self.added_handlers = []

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
    def result_var(self):
        """
        Returns the result var of the current function or the current alias for
        it.
        """
        if self.var_aliases and RESULT_NAME in self.var_aliases:
            return self.var_aliases[RESULT_NAME].ref
        if self.current_function.result:
            return self.current_function.result.ref
        return None

    @property
    def error_var(self):
        """
        Returns the error var of the current function or the current alias for
        it.
        """
        if self.var_aliases and ERROR_NAME in self.var_aliases:
            return self.var_aliases[ERROR_NAME].ref
        return self.current_function.error_var

    def get_label_name(self, name: str) -> str:
        """
        Returns the actual name of the given label in the current context, i.e.,
        looks for aliases.
        """
        if name in self.label_aliases:
            return self.label_aliases[name]
        return name
