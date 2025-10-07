# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# compares two classes each
class E:
    def __init__(self, i: int, j: int) -> None:
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.i is i and self.j is j))
        self.i: int = i
        self.j: int = j
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                type(self) == type(other), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(E, other).i and self.j == cast(E, other).j)
                        )
                    )
                )
            )
        )
        Ensures(
            Implies(
                type(other) == F, Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(F, other).i and self.j == cast(F, other).j)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif type(self) == type(other):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(E, other).i and self.j == cast(E, other).j
                )
            )
        elif type(other) == F:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(F, other).i and self.j == cast(F, other).j 
                )
            )
        return False

    @Pure
    def __hash__(self) -> int:
        Requires(Acc(self.state()))
        Ensures(Result() == Unfolding(self.state(), hash((self.i, self.j))))
        return Unfolding(self.state(), hash((self.i, self.j)))

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.j)

class F:
    def __init__(self, i: int, j: int) -> None:
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.i is i and self.j is j))
        self.i: int = i
        self.j: int = j
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                type(self) == type(other), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(F, other).i and self.j == cast(F, other).j)
                        )
                    )
                )
            )
        )
        Ensures(
            Implies(
                type(other) == E, Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(E, other).i and self.j == cast(E, other).j)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif type(self) == type(other):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(F, other).i and self.j == cast(F, other).j
                )
            )
        elif type(other) == E:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(E, other).i and self.j == cast(E, other).j
                )
            )
        return False

    @Pure
    def __hash__(self) -> int:
        Requires(Acc(self.state()))
        Ensures(Result() == Unfolding(self.state(), hash((self.i, self.j))))
        return Unfolding(self.state(), hash((self.i, self.j)))

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.j)

e1: E = E(42, 41)
e2: F = F(42, 41)
assert e1 == e2
assert hash(e1) == hash(e2)