from py2viper_translation.lib.context import Context


class SIFContext(Context):
    def __init__(self):
        super().__init__()
        self._use_prime = False

    @property
    def use_prime(self) -> bool:
        return self._use_prime

    @use_prime.setter
    def use_prime(self, prime: bool):
        self._use_prime = prime
        if prime:
            self.var_aliases = {k: v.var_prime for (k, v) in
                                self.get_all_vars()}
        else:
            self.var_aliases = {}

