# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# # only one class each
# class A1:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         if self is other:
#             return True
#         return False
# 
# class B1:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         if type(self) == type(other):
#             return True
#         return False
#     
# class C1:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(isinstance(other, C1), Result())
#         )
#         if isinstance(other, C1):
#             return True
#         return False

# one class but with fields
class H1:
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
                    Result() == (self.i == cast(H1, other).i and 
                                 self.s == cast(H1, other).s and 
                                 self.b == cast(H1, other).b)
                )
            )
        ))
        if type(self) == type(other):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(H1, other).i and 
                    self.s == cast(H1, other).s and 
                    self.b == cast(H1, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)


# # reflexivity/symmetry/transitivity with no fields
# class A:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(type(self) == type(other) or type(other) == B or type(other) == C or self is other, Result())
#         )
#         if type(self) == type(other) or type(other) == B or type(other) == C or self is other:
#             return True
#         return False
# 
# class B:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(type(self) == type(other) or type(other) == A or type(other) == C or self is other, Result())
#         )
#         if type(self) == type(other) or type(other) == A or type(other) == C or self is other:
#             return True
#         return False
# 
# class C:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(type(self) == type(other) or type(other) == A or type(other) == B or self is other, Result())
#         )
#         if type(self) == type(other) or type(other) == A or type(other) == B or self is other:
#             return True
#         return False

# # reflexivity/symmetry/transitivity with no fields
# class AS:
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(type(other) == AS or type(other) == BS or type(other) == CS or self is other, Result())
#         )
#         if type(other) == AS or type(other) == BS or type(other) == CS or self is other:
#             return True
#         return False
# 
# class BS(AS):
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(type(other) == AS or type(other) == BS or type(other) == CS or self is other, Result())
#         )
#         if type(other) == AS or type(other) == BS or type(other) == CS or self is other:
#             return True
#         return False
# 
# class CS(AS):
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(
#             Implies(type(other) == AS or type(other) == BS or type(other) == CS or self is other, Result())
#         )
#         if type(other) == AS or type(other) == BS or type(other) == CS or self is other:
#             return True
#         return False
    


# # same but with multiple fields
# class G:
#     def __init__(self, i: int, s: str, b: bool) -> None:
#         self.i: int = i
#         self.s: str = s
#         self.b: bool = b
#         Fold(state_pred(self))
#         Ensures(state_pred(self))
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(
#             type(self) == type(other),
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(G, other).i and 
#                                  self.s == cast(G, other).s and 
#                                  self.b == cast(G, other).b)
#                 )
#             )
#         ))
#         Ensures(Implies(
#             type(other) == H,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(H, other).i and 
#                                  self.s == cast(H, other).s and 
#                                  self.b == cast(H, other).b)
#                 )
#             )
#         ))
#         Ensures(Implies(
#             type(other) == I,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(I, other).i and 
#                                  self.s == cast(I, other).s and 
#                                  self.b == cast(I, other).b)
#                 )
#             )
#         ))
#         if type(self) == type(other):
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(G, other).i and 
#                     self.s == cast(G, other).s and 
#                     self.b == cast(G, other).b
#                 )
#             )
#         elif type(other) == H:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(H, other).i and 
#                     self.s == cast(H, other).s and 
#                     self.b == cast(H, other).b
#                 )
#             )
#         elif type(other) == I:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(I, other).i and 
#                     self.s == cast(I, other).s and 
#                     self.b == cast(I, other).b
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.i) and Acc(self.s) and Acc(self.b)
# 
# class H:
#     def __init__(self, i: int, s: str, b: bool) -> None:
#         self.i: int = i
#         self.s: str = s
#         self.b: bool = b
#         Fold(state_pred(self))
#         Ensures(state_pred(self))
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(
#             type(self) == type(other),
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(H, other).i and 
#                                  self.s == cast(H, other).s and 
#                                  self.b == cast(H, other).b)
#                 )
#             )
#         ))
#         Ensures(Implies(
#             type(other) == G,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(G, other).i and 
#                                  self.s == cast(G, other).s and 
#                                  self.b == cast(G, other).b)
#                 )
#             )
#         ))
#         Ensures(Implies(
#             type(other) == I,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(I, other).i and 
#                                  self.s == cast(I, other).s and 
#                                  self.b == cast(I, other).b)
#                 )
#             )
#         ))
#         if type(self) == type(other):
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(H, other).i and 
#                     self.s == cast(H, other).s and 
#                     self.b == cast(H, other).b
#                 )
#             )
#         elif type(other) == G:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(G, other).i and 
#                     self.s == cast(G, other).s and 
#                     self.b == cast(G, other).b
#                 )
#             )
#         elif type(other) == I:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(I, other).i and 
#                     self.s == cast(I, other).s and 
#                     self.b == cast(I, other).b
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.i) and Acc(self.s) and Acc(self.b)
# 
# class I:
#     def __init__(self, i: int, s: str, b: bool) -> None:
#         self.i: int = i
#         self.s: str = s
#         self.b: bool = b
#         Fold(state_pred(self))
#         Ensures(state_pred(self))
# 
#     @Pure
#     def __eq__(self, other: object) -> bool:
#         Requires(state_pred(self))
#         Requires(Implies(not Stateless(other), state_pred(other)))
#         Ensures(Implies(
#             type(self) == type(other),
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(I, other).i and 
#                                  self.s == cast(I, other).s and 
#                                  self.b == cast(I, other).b)
#                 )
#             )
#         ))
#         Ensures(Implies(
#             type(other) == G,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(G, other).i and 
#                                  self.s == cast(G, other).s and 
#                                  self.b == cast(G, other).b)
#                 )
#             )
#         ))
#         Ensures(Implies(
#             type(other) == H,
#             Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     Result() == (self.i == cast(H, other).i and 
#                                  self.s == cast(H, other).s and 
#                                  self.b == cast(H, other).b)
#                 )
#             )
#         ))
#         if type(self) == type(other):
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(I, other).i and 
#                     self.s == cast(I, other).s and 
#                     self.b == cast(I, other).b
# 
#                 )
#             )
#         elif type(other) == G:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(G, other).i and 
#                     self.s == cast(G, other).s and 
#                     self.b == cast(G, other).b
#                 )
#             )
#         elif type(other) == H:
#             return Unfolding(self.state(),
#                 Unfolding(state_pred(other),
#                     self.i == cast(H, other).i and 
#                     self.s == cast(H, other).s and 
#                     self.b == cast(H, other).b
#                 )
#             )
#         return False
# 
#     @Predicate
#     def state(self) -> bool:
#         return Acc(self.i) and Acc(self.s) and Acc(self.b)