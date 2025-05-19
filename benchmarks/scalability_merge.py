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
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(A, other).i)
                        )
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

class B:
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
                isinstance(other, B), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(B, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, B):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(B, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class C:
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
                isinstance(other, C), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(C, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, C):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(C, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class D:
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
                isinstance(other, D), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(D, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, D):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(D, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class E:
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
                isinstance(other, E), Unfolding(
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
        elif isinstance(other, E):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(E, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class F:
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
                isinstance(other, F), Unfolding(
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
        elif isinstance(other, F):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(F, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class G:
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
                isinstance(other, G), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(G, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, G):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(G, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)
    
def foo(o1: object, o2: object) -> int:
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
    assert o1 == o2
    return 0