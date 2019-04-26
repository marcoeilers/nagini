# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/largerExamples/parallelTreeProcessing.chalice`` test from
Chalice2Silver test suite.

.. note::

    Python version is sequential because fork is not supported yet.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Requires,
    Invariant,
    Implies,
    Predicate,
    Fold,
    Ensures,
    Unfold,
    Unfolding,
)
from nagini_contracts.obligations import *


class Tree:

    @Predicate
    def valid(self) -> bool:
        return (Acc(self.left) and Acc(self.right) and
                Acc(self.height, 1/10) and self.height >= 0 and
                Implies(
                    self.left is not None,
                    self.left.valid() and Acc(self.left.height, 1/10) and
                    self.left.height == self.height - 1) and
                Implies(
                    self.right is not None,
                    self.right.valid() and Acc(self.right.height, 1/10) and
                    self.right.height == self.height - 1)
                )

    def __init__(self, left: 'Tree', right: 'Tree', height: int) -> None:
        Requires(left.valid() and Acc(left.height, 1/10) and
                 left.height == height-1)
        Requires(right.valid() and Acc(right.height, 1/10) and
                 right.height == height-1)
        Requires(height >= 0)
        Ensures(self.valid())
        self.left = left        # type: Tree
        self.right = right      # type: Tree
        self.height = height    # type: int
        Fold(self.valid())


    def work(self, call_height: int) -> None:
        Requires(self.valid())
        Requires(call_height >= 0)
        Requires(Unfolding(self.valid(), self.height == call_height))
        Requires(MustTerminate(call_height + 1))
        Ensures(self.valid())

        if call_height > 0:
            Unfold(self.valid())
            if self.left is not None:
                self.left.work(call_height - 1)
            if self.right is not None:
                self.right.work(call_height - 1)
            Fold(self.valid())
