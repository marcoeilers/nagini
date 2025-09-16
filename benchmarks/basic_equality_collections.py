# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List, Set, Dict

# class A:
#     def __init__(self, i: int, s: str, b: bool) -> None:
#         self.i: int = i
#         self.s: str = s
#         self.b: bool = b
#         Fold(self.state())
#         Ensures(self.state())
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(
#             self is other or type(other) == A,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(A, other).i and 
#                                  self.s == cast(A, other).s and 
#                                  self.b == cast(A, other).b)
#                 )
#             )
#         ))
#         if self is other or type(other) == A:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(A, other).i and 
#                     self.s == cast(A, other).s and 
#                     self.b == cast(A, other).b
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.i) and Acc(self.s) and Acc(self.b)


class D1:
    def __init__(self, l: List[int]) -> None:
        Requires(state_pred(l))
        Ensures(self.state())
        # we need reference equality here
        Ensures(Unfolding(self.state(), self.l == l))
        self.l: List[int] = l

        # self.s: Set[A] = set()
        # Fold(state_pred(self.l))
        # Fold(state_pred(self.s))
        Fold(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            self is other or type(other) == D1,
            Result() ==
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.l == cast(D1, other).l # and self.s == cast(D1, other).s)
                )
            )
        ))
        if self is other or type(other) == D1:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.l == cast(D1, other).l # and self.s == cast(D1, other).s
            ))
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.l) and Acc(state_pred(self.l)) # and Acc(self.s) and Acc(state_pred(self.s))

ints_1: List[int] = [1,2,3,42]
ints_2: List[int] = [1,2,3,42]
Fold(state_pred(ints_1))
Fold(state_pred(ints_2))
one: D1 = D1(ints_1)
two: D1 = D1(ints_2)
assert one == two



# def foo(one: D1, two: D1):
#     Requires(one.state())
#     Requires(two.state())
#     Ensures(one.state())
#     Ensures(two.state())
# 
#     Unfold(one.state())
#     Unfold(two.state())
# 
#     assert 
# 
#     Fold(one.state())
#     Fold(two.state())