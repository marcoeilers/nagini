# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# Usability:
# All LOC: 193
# Without state/folding LOC: 160
# Factor: 1.20625


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

# same as A
class B(A):
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

# mutual recursion
class C:
    def __init__(self) -> None:
        Fold(state_pred(self))
        Ensures(state_pred(self))

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(other) == C or type(other) == D or self is other, Result())
        )
        if type(other) == C or type(other) == D or self is other:
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
            Implies(type(other) == C or type(other) == D or self is other, Result())
        )
        if type(other) == C or type(other) == D or self is other:
            return True
        return False


# symmetry with fields
# True iff also instance of E with same fields
class E:
    def __init__(self, i: int) -> None:
        self.i: int = i

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
                            Result() == (self.i == cast(E, other).i)
                        )
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
                    self.i == cast(E, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

# symmetry with multiple fields; two classes mutually naming each other
class G:
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
                    Result() == (self.i == cast(G, other).i and 
                                 self.s == cast(G, other).s and 
                                 self.b == cast(G, other).b)
                )
            )
        ))
        Ensures(Implies(
            type(other) == H,
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
                    self.i == cast(G, other).i and 
                    self.s == cast(G, other).s and 
                    self.b == cast(G, other).b
                )
            )
        elif type(other) == H:
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
        Ensures(Implies(
            type(other) == G,
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(G, other).i and 
                                 self.s == cast(G, other).s and 
                                 self.b == cast(G, other).b)
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
        elif type(other) == G:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(G, other).i and 
                    self.s == cast(G, other).s and 
                    self.b == cast(G, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)


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
