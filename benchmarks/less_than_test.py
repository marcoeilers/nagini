# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# This works:))) (with merge function)
class E:
    def __init__(self, i: int) -> None:
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.i == i))
        self.i: int = i
        Fold(self.state())

    @Pure
    def __lt__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, not Result()))
        Ensures(
            Implies(
                type(self) == type(other), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i < cast(E, other).i)
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
                            Result() == (self.i < cast(F, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return False
        elif type(self) == type(other):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i < cast(E, other).i
                )
            )
        elif type(other) == F:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i < cast(F, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i)

class F:
    def __init__(self, i: int) -> None:
        Ensures(self.state())
        Ensures(Unfolding(self.state(), self.i == i))
        self.i: int = i
        Fold(self.state())

    @Pure
    def __lt__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, not Result()))
        Ensures(
            Implies(
                type(self) == type(other), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i < cast(F, other).i)
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
                            Result() == (self.i < cast(E, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return False
        elif type(self) == type(other):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i < cast(F, other).i
                )
            )
        elif type(other) == E:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i < cast(E, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i)

ee = E(42)
ff = F(52)
assert ee < ff