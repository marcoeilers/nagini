# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List

# only one class each

# no fields
class A1:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        if self is other:
            return True
        return False

class B1:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        if type(self) == type(other):
            return True
        return False
    
class C1:
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(isinstance(other, C1), Result())
        )
        if isinstance(other, C1):
            return True
        return False
    
# one class but with multiple fields
class D1:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            self is other,
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(D1, other).i and 
                                 self.s == cast(D1, other).s and 
                                 self.b == cast(D1, other).b)
                )
            )
        ))
        if self is other:
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(D1, other).i and 
                    self.s == cast(D1, other).s and 
                    self.b == cast(D1, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)

class E1:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            type(self) == type(other),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(E1, other).i and 
                                 self.s == cast(E1, other).s and 
                                 self.b == cast(E1, other).b)
                )
            )
        ))
        if type(self) == type(other):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(E1, other).i and 
                    self.s == cast(E1, other).s and 
                    self.b == cast(E1, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)

class F1:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, F1),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(F1, other).i and 
                                 self.s == cast(F1, other).s and 
                                 self.b == cast(F1, other).b)
                )
            )
        ))
        if isinstance(other, F1):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(F1, other).i and 
                    self.s == cast(F1, other).s and 
                    self.b == cast(F1, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)

# inherited 
class AI(A1):
    pass

class BI(B1):
    pass
    
class CI(C1):
    pass

class DI(D1):
    pass

class EI(E1):
    pass

class FI(F1):
    pass
