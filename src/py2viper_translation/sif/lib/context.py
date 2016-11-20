from typing import Dict

from py2viper_translation.lib.context import Context
from py2viper_translation.lib.program_nodes import PythonVar
from py2viper_translation.lib.typedefs import Expr
from py2viper_translation.sif.lib.program_nodes import SIFPythonVar, TL_VAR_NAME


class SIFContext(Context):
    def __init__(self):
        super().__init__()
        self._use_prime = False
        self._old_vars = {}
        self._curr_tl_var_expr = None  # Current timeLevel expression
        self.in_pres = False
        self.in_posts = False

    @property
    def use_prime(self) -> bool:
        return self._use_prime

    def set_prime_ctx(self, aliases: Dict[str, PythonVar] = None):
        assert not self._use_prime
        self._use_prime = True
        if self.var_aliases:
            # var_alias was already set. We back it up and add update with new
            # aliases.
            self._old_vars = self.var_aliases.copy()
        if not aliases:
            aliases = {k:v.var_prime for (k, v) in self.get_all_vars() if
                       isinstance(v, SIFPythonVar)}

        self.var_aliases.update(aliases)

    def set_normal_ctx(self):
        assert self._use_prime
        self._use_prime = False
        # Restore from backed up aliases.
        self.var_aliases = self._old_vars
        self._old_vars = {}

    def reset(self):
        self._use_prime = False
        self._old_vars = {}
        self.var_aliases = {}
        self._curr_tl_var_expr = None

    @property
    def current_tl_var_expr(self) -> Expr:
        if self._curr_tl_var_expr:
            return self._curr_tl_var_expr
        elif self.in_pres:
            return self.actual_function.tl_var.ref()
        elif TL_VAR_NAME in self.var_aliases:
            return self.var_aliases[TL_VAR_NAME].ref()
        elif self.actual_function.pure:
            return self.actual_function.tl_var.ref()
        else:
            return self.actual_function.new_tl_var.ref()

    @current_tl_var_expr.setter
    def current_tl_var_expr(self, expr: Expr):
        self._curr_tl_var_expr = expr
