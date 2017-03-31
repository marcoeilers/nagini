"""
This test is a ported version of
``obligations/christian/lt_fib.chalice`` test from Chalice2Silver test
suite.
"""


from nagini_contracts.contracts import (
    Requires,
)
from nagini_contracts.obligations import *


class A:

    def fib(self, n: int) -> int:
        Requires(MustTerminate(n))
        if n <= 1:
            return 1
        elif n == 2:
            return 2
        else:
            w = self.fib(n - 1)
            v = self.fib(n - 2)
            return v + w
