from typing import Dict

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import PythonVar


class SIFContext(Context):
    def __init__(self):
        super().__init__()
        self._use_prime = False
        self._old_vars = {}

    @property
    def use_prime(self) -> bool:
        return self._use_prime

    def set_prime_ctx(self, aliases: Dict[str, PythonVar] = None,
                      backup: bool = False):
        assert not self._use_prime
        self._use_prime = True
        if backup:
            self._old_vars = self.var_aliases
        if aliases:
            self.var_aliases = aliases
        else:
            self.var_aliases = {k: v.var_prime for (k, v) in
                                self.get_all_vars()}

    def set_normal_ctx(self, restore=False):
        assert self._use_prime
        self._use_prime = False
        if restore:
            self.var_aliases = self._old_vars
            self._old_vars = {}
        else:
            self.var_aliases = {}
