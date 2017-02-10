from py2viper_translation.lib.typedefs import Expr
from typing import Optional


class ExprCache:
    """
    Container for the results of an already translated expression.
    """
    def __init__(self):
        self._results = []
        self._idx = 0

    def next(self) -> Optional[Expr]:
        """
        Returns the next result expr or None if there are no more available.
        """
        res = None
        if self._idx < len(self._results):
            res = self._results[self._idx]
            self._idx += 1

        return res

    def add_result(self, result: Expr):
        self._results.append(result)

    def __len__(self) -> int:
        return len(self._results)
