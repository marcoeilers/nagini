# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast


# mutual recursion with B <: A
class A:
    def __init__(self) -> None:
        Fold(state_pred(self))
        Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(other) == A or type(other) == B or self is other, Result())
        )
        if type(other) == A or type(other) == B or self is other:
            return True
        return False

# inherited from A
class B(A):
    pass

# mutual recursion with tuples
class C:
    def __init__(self) -> None:
        Fold(state_pred(self))
        Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(other) in (C, D) or self is other, Result())
        )
        if type(other) in (C, D) or self is other:
            return True
        return False

class D:
    def __init__(self) -> None:
        Fold(state_pred(self))
        Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(other) in (C, D) or self is other, Result())
        )
        if type(other) in (C, D) or self is other:
            return True
        return False

# symmetry with fields
# not subtypes
class E:
    def __init__(self, i: int) -> None:
        self.i: int = i

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(
                self is other, Unfolding(
                    self.state(), 
                    Result() == (self.i == cast(E, other).i)
                )
            )
        )
        Ensures(
            Implies(
                type(self) == type(other), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other),
                        Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(E, other).i)
                        )
                    )
                )
            )
        )
        # Ensures(
        #     Implies(
        #         type(other) == E or self is other, 
        #         Result() == (
        #             Unfolding(
        #                 self.state(),
        #                 Implies(not Stateless(other), Unfolding(
        #                     state_pred(other),
        #                     self.i == cast(E, other).i
        #                 ))
        #             )
        #         )
        #     )
        # )
        # Ensures(
        #     Implies(
        #         type(other) == F,
        #         Result() == (
        #             Unfolding(
        #                 self.state(),
        #                 Implies(not Stateless(other), Unfolding(
        #                     state_pred(other),
        #                     self.i == cast(F, other).j
        #                 ))
        #             )
        #         )
        #     )
        # )
        if self is other:
            return Unfolding(
                self.state(),
                self.i == cast(E, other).i
            )
        elif type(self) == type(other):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(E, other).i
                )
            )
        #elif type(other) == F:
        #    return Unfolding(
        #        self.state(),
        #        Unfolding(
        #            state_pred(other),
        #            self.i == cast(F, other).j
        #        )
        #    )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

# class F:
#     def __init__(self, j: int) -> None:
#         self.j: int = j
#         Fold(state_pred(self))
#         Ensures(state_pred(self))
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(
#                 type(other) == E,
#                 Result() == (
#                     Unfolding(
#                         self.state(),
#                         Implies(not Stateless(other), Unfolding(
#                             state_pred(other),
#                             self.j == cast(E, other).i
#                         ))
#                     )
#                 )
#             )
#         )
#         Ensures(
#             Implies(
#                 type(other) == F or self is other,
#                 Result() == (
#                     Unfolding(
#                         self.state(),
#                         Implies(not Stateless(other), Unfolding(
#                             state_pred(other),
#                             self.j == cast(F, other).j
#                         ))
#                     )
#                 )
#             )
#         )
#         if type(other) == E:
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.j == cast(E, other).i
#                 )
#             )
#         elif type(other) == F or self is other:
#             return Unfolding(
#                 self.state(),
#                 Unfolding(
#                     state_pred(other),
#                     self.j == cast(F, other).j
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Wildcard(self.j)


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
