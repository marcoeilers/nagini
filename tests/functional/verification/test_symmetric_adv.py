# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# TODO: add tests, which should fail

# compare A and B with fields
class A:
    def __init__(self, j: int) -> None:
        self.j: int = j
        Fold(state_pred(self))
        Ensures(state_pred(self))

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
                            Result() == (self.j == cast(A, other).j)
                        )
                    )
                )
            )
        )
        # Ensures(
        #     Implies(
        #         type(other) == E, Unfolding(
        #             self.state(),
        #             Implies(
        #                 not Stateless(other), Unfolding(
        #                 state_pred(other),
        #                 Result() == (self.j == cast(E, other).i)
        #             ))
        #         )
        #     )
        # )
        if self is other:
            return True
        elif type(self) == type(other):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.j == cast(A, other).j
                )
            )
        elif type(other) == B:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.j == cast(B, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.j)

class B:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(state_pred(self))
        Ensures(state_pred(self))

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
                            Result() == (self.i == cast(B, other).i)
                        )
                    )
                )
            )
        )
        Ensures(
            Implies(
                type(other) == A, Unfolding(
                    self.state(),
                    Unfolding(
                        state_pred(other),
                        Result() == (self.i == cast(A, other).j)
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
                    self.i == cast(B, other).i
                )
            )
        elif type(other) == A:
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(A, other).j
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and 


# TODO: caller learn symmetry



# def foo(a: A, b: A) -> int:
#     Requires(state_pred(a))
#     Requires(state_pred(b))
#     Requires(Unfolding(
#         state_pred(a),
#         a == b
#     ))
#     Ensures(state_pred(a))
#     Ensures(state_pred(b))
#     return 0
# 
# a = A()
# a_ = a
# Unfold(state_pred(a))
# Unfold(state_pred(a_))
# foo(a, a_)
# Fold(state_pred(a))
# Fold(state_pred(a_))
