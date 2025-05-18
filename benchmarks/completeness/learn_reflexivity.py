# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

class A:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b
        Fold(state_pred(self))
        Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(Result(), self is other))
        if self is other:
            return True
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)

def foo(a: A, b: A) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Requires(Unfolding(
        state_pred(a),
        Unfolding(
            state_pred(b),
            a == b
        )
    ))
    Ensures(state_pred(a))
    Ensures(state_pred(b))
    # learn reflexivity from call: a == b
    Ensures(a is b)
    return 0

a = A(42, "python", True)
a_ = a
Unfold(state_pred(a))
Unfold(state_pred(a_))
foo(a, a_)
Fold(state_pred(a))
Fold(state_pred(a_))