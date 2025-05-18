# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List

# Usability:
# All LOC: 61
# Without state/folding LOC: 49
# Factor: 1.2448979591836735

class A:
    def __init__(self) -> None:
        # Fold(state_pred(self))
        # Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        if self is other:
            return True
        return False
        

# clearly reflexive
class D:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        if type(self) == type(other):
            return True
        return False
    
class F:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(isinstance(other, F), Result())
        )
        if isinstance(other, F):
            return True
        return False

class H:
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
        Ensures(Implies(
            type(self) == type(other),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(H, other).i and 
                                 self.s == cast(H, other).s and 
                                 self.b == cast(H, other).b)
                )
            )
        ))
        if type(self) == type(other):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(H, other).i and 
                    self.s == cast(H, other).s and 
                    self.b == cast(H, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)

# TODO: fix -> what is missing?
# class G:
#     def __init__(self) -> None:
#         self.i: int = 1
#         self.a: List[int] = []
#         Fold(state_pred(self))
#         Ensures(state_pred(self))
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(self is other, Result())
#         )
#         if type(self) == type(other):
#             return Unfolding(state_pred(self),
#                 Unfolding(state_pred(other),
#                     self.i == cast(G, other).i and
#                     self.a == cast(G, other).a
#                 )
#             )
#         return False
#     
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.i) and Acc(self.a)



    


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
# 