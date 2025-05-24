# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

class A:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, A), Unfolding(
                    self.state(),
                    Unfolding(
                        state_pred(other),
                        Result() == (self.i == cast(A, other).i)
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, A):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(A, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

def fooA(o1: object, o2: object) -> int:
    Requires(isinstance(o1, A))
    Requires(isinstance(o2, A))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(A, o1).i == cast(A, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))

    Unfold(state_pred(o1))
    Unfold(state_pred(o2))
    assert o1 == o2
    Fold(state_pred(o1))
    Fold(state_pred(o2))
    return 0