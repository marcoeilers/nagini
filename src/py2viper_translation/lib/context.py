from py2viper_translation.lib.constants import ERROR_NAME, RESULT_NAME
from py2viper_translation.lib.program_nodes import PythonVar
from typing import List


class Context:
    """
    Contains the current state of the entire translation process.
    """

    def __init__(self) -> None:
        self.current_function = None
        self.current_class = None
        self.var_aliases = None
        self.label_aliases = {}
        self.position = None
        self.info = None
        self.program = None
        self.inlined_calls = []
        self.ignore_family_folds = False

    def get_all_vars(self) -> List[PythonVar]:
        res = []
        if self.current_function:
            res += list(self.current_function.locals.items())
            res += list(self.current_function.args.items())
        if self.program:
            res += list(self.program.global_vars.items())

        return res

    @property
    def actual_function(self):
        if not self.inlined_calls:
            return self.current_function
        return self.inlined_calls[-1]

    @property
    def result_var(self):
        if self.var_aliases and RESULT_NAME in self.var_aliases:
            return self.var_aliases[RESULT_NAME].ref
        return self.current_function.result.ref

    @property
    def error_var(self):
        if self.var_aliases and ERROR_NAME in self.var_aliases:
            return self.var_aliases[ERROR_NAME].ref
        return self.current_function.error_var

    def get_label_name(self, name: str) -> str:
        if name in self.label_aliases:
            return self.label_aliases[name]
        return name
