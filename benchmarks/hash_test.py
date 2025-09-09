# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# compares two classes each

class E:
    def __init__(self, i: int) -> None:
        Ensures(Acc(self.i))
        self.i: int = i

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
                            Result() == (self.i == cast(E, other).i)
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
                            Result() == (self.i == cast(F, other).i)
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
                    self.i == cast(E, other).i
                )
            )
        elif type(other) == F:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(F, other).i
                )
            )
        return False

    @Pure
    def __hash__(self) -> int:
        Requires(Acc(self.state()))
        return Unfolding(self.state(), hash(self.i))

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class F:
    def __init__(self, i: int) -> None:
        self.i: int = i

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
                            Result() == (self.i == cast(F, other).i)
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
                            Result() == (self.i == cast(E, other).i)
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
                    self.i == cast(F, other).i
                )
            )
        elif type(other) == E:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(E, other).i
                )
            )
        return False

    @Pure
    def __hash__(self) -> int:
        Requires(Acc(self.state()))
        return Unfolding(self.state(), hash(self.i))

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)
