# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

class A:
    def __init__(self, i: int) -> None:
        self.i: int = i

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(
                isinstance(other, A),
                Unfolding(self.state(),
                    Unfolding(state_pred(other),
                        Implies(
                            Result(),
                            self.i == cast(A, other).i
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, A):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(A, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i)

class B(A):
    def __init__(self, i: int, j: int) -> None:
        self.i: int = i
        self.j: int = j

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(
                isinstance(other, A),
                Unfolding(self.state(),
                    Unfolding(state_pred(other),
                        Implies(
                            Result(),
                            self.i == cast(A, other).i
                        )
                    )
                )
            )
        )
        Ensures(
            Implies(
                type(other) == B,
                Unfolding(self.state(),
                    Unfolding(state_pred(other),
                        Implies(
                            Result(),
                            self.i == cast(B, other).i and self.j == cast(B, other).j
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif type(other) == B:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(B, other).i and self.j == cast(B, other).j
                )
            )
        elif isinstance(other, A):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(A, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.j)

# dynamic type is B for b1 and b2
def client(b1: B, b2: A) -> int:
    Requires(state_pred(b1))
    Requires(state_pred(b2))
    Ensures(state_pred(b1))
    Ensures(state_pred(b2))

    # with the extended function we only learn much about 
    # b1, which has static type B
    Unfold(state_pred(b1))
    Unfold(state_pred(b2))
    res: bool = (b1 == b2)
    if res and type(b2) == B:
        assert b1.i == b2.i
        assert b1.j == cast(B, b2).j  # not provable by the extended function

    Fold(state_pred(b1))
    Fold(state_pred(b2))
    return 0