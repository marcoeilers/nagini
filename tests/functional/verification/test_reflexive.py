# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List


class A:
    def __init__(self) -> None:
        Fold(state_pred(self))
        Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        if self is other:
            return True
        return False
        
# reflexivity postcodition is violated:
# ensures self == other ==> result
class B:
    @Pure
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        return False

# modularity postcondition is violated:
# ensures result ==> type(self) == type(other) (mentioned set M_C is empty)
class C:
    @Pure
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        return True
    
# clearly reflexive
class D:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        if type(self) == type(other):
            return True
        return False
    
# We do not know the exact type of self, only that it's 
# an instance of E
class E:
    @Pure
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(other) == E, Result())
        )
        if type(other) == E:
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


# TODO: fix -> should work like this right?
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
#         Requires(state_pred(self.a))  # correct like this?
#         Ensures(
#             Implies(self is other, Result())
#         )
#         if type(self) == type(other):
#             return Unfolding(state_pred(self),
#                 Unfolding(state_pred(other),
#                     Unfolding(state_pred(self.a),
#                         self.i == cast(G, other).i and
#                         self.a == cast(G, other).a
#                     )
#                 )
#             )
#         return False
#     
#     @Predicate
#     def state(self) -> bool:
#         return Wildcard(self.i)



    


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