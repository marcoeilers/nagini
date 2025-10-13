# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast


class A:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(self) == type(other) or type(other) == B or type(other) == C or self is other or 
            type(other) == D, Result())
        )
        if (type(self) == type(other) or type(other) == B or type(other) == C or self is other or 
            type(other) == D):
            return True
        return False

class B:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(self) == type(other) or type(other) == A or type(other) == C or self is other or 
            type(other) == D, Result())
        )
        if (type(self) == type(other) or type(other) == A or type(other) == C or self is other or 
            type(other) == D):
            return True
        return False

class C:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(self) == type(other) or type(other) == B or type(other) == A or self is other or 
            type(other) == D, Result())
        )
        if (type(self) == type(other) or type(other) == B or type(other) == A or self is other or 
            type(other) == D):
            return True
        return False

class D:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(self) == type(other) or type(other) == B or type(other) == C or self is other or 
            type(other) == A, Result())
        )
        if (type(self) == type(other) or type(other) == B or type(other) == C or self is other or 
            type(other) == A):
            return True
        return False


# # # TODO: caller learn symmetry
# # 
# # 
# # 
# # # def foo(a: A, b: A) -> int:
# # #     Requires(state_pred(a))
# # #     Requires(state_pred(b))
# # #     Requires(Unfolding(
# # #         state_pred(a),
# # #         a == b
# # #     ))
# # #     Ensures(state_pred(a))
# # #     Ensures(state_pred(b))
# # #     return 0
# # # 
# # # a = A()
# # # a_ = a
# # # Unfold(state_pred(a))
# # # Unfold(state_pred(a_))
# # # foo(a, a_)
# # # Fold(state_pred(a))
# # # Fold(state_pred(a_))
# # 