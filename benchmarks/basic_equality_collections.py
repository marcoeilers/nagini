# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List, Set, Dict

class A:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            self is other or type(other) == A,
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(A, other).i and 
                                 self.s == cast(A, other).s and 
                                 self.b == cast(A, other).b)
                )
            )
        ))
        if self is other or type(other) == A:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(A, other).i and 
                    self.s == cast(A, other).s and 
                    self.b == cast(A, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)


class D1:
    def __init__(self, s: Set[A]) -> None:
        self.l: List[int] = [1,2,3]
        self.s: Set[A] = s

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            self is other or type(other) == D1,
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.l == cast(D1, other).l and 
                                 self.s == cast(D1, other).s)
                )
            )
        ))
        if self is other or type(other) == D1:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.l == cast(D1, other).l and
                    self.s == cast(D1, other).s
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.l) and Acc(state_pred(self.l)) and Acc(self.s) and Acc(state_pred(self.s))