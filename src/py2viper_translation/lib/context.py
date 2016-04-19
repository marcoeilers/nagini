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
        self.position = None
        self.info = None
        self.program = None

    def get_all_vars(self) -> List[PythonVar]:
        res = []
        if self.current_function:
            res += list(self.current_function.locals.items())
            res += list(self.current_function.args.items())
        if self.program:
            res += list(self.program.global_vars.items())

        return res
