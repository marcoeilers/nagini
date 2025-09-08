# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List, Set, Dict

class E:
    def __init__(self, l: List[int]) -> None:
        Requires(state_pred(l))
        Ensures(self.state())
        # must be reference equality
        Ensures(Unfolding(self.state(), self.l is l))
        self.l: List[int] = l
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
                            Result() == (self.l == cast(E, other).l)
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
                            Result() == (self.l == cast(F, other).l)
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
                    self.l == cast(E, other).l
                )
            )
        elif type(other) == F:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.l == cast(F, other).l
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.l) and Acc(state_pred(self.l))

class F:
    def __init__(self, l: List[int]) -> None:
        Requires(state_pred(l))
        Ensures(self.state())
        # must be reference equality
        Ensures(Unfolding(self.state(), self.l is l))
        self.l: List[int] = l
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
                            Result() == (self.l == cast(F, other).l)
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
                            Result() == (self.l == cast(E, other).l)
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
                    self.l == cast(F, other).l
                )
            )
        elif type(other) == E:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.l == cast(E, other).l
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.l) and Acc(state_pred(self.l))


ints_1: List[int] = [1,2,3,42]
ints_2: List[int] = [1,2,3,42]
Fold(state_pred(ints_1))
Fold(state_pred(ints_2))
one: E = E(ints_1)
two: F = F(ints_2)
assert one == two

Unfold(state_pred(one))
Unfold(state_pred(two))

assert 42 in one.l
assert 3 in two.l