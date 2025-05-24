# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

# Usability:
# All LOC: 336
# Without state/folding LOC: 240
# Factor: 1.4

class A:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, A),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(A, other).i and 
                                 self.s == cast(A, other).s and 
                                 self.b == cast(A, other).b)
                )
            )
        ))
        if isinstance(other, A):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(A, other).i and 
                    self.s == cast(A, other).s and 
                    self.b == cast(A, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooA(a: A, b: A) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(A, a).i == cast(A, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class B:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, B),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(B, other).i and 
                                 self.s == cast(B, other).s and 
                                 self.b == cast(B, other).b)
                )
            )
        ))
        if isinstance(other, B):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(B, other).i and 
                    self.s == cast(B, other).s and 
                    self.b == cast(B, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooB(a: B, b: B) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(B, a).i == cast(B, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class C:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, C),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(C, other).i and 
                                 self.s == cast(C, other).s and 
                                 self.b == cast(C, other).b)
                )
            )
        ))
        if isinstance(other, C):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(C, other).i and 
                    self.s == cast(C, other).s and 
                    self.b == cast(C, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooC(a: C, b: C) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(C, a).i == cast(C, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class D:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, D),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(D, other).i and 
                                 self.s == cast(D, other).s and 
                                 self.b == cast(D, other).b)
                )
            )
        ))
        if isinstance(other, D):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(D, other).i and 
                    self.s == cast(D, other).s and 
                    self.b == cast(D, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooD(a: D, b: D) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(D, a).i == cast(D, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class E:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, E),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(E, other).i and 
                                 self.s == cast(E, other).s and 
                                 self.b == cast(E, other).b)
                )
            )
        ))
        if isinstance(other, E):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(E, other).i and 
                    self.s == cast(E, other).s and 
                    self.b == cast(E, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooE(a: E, b: E) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(E, a).i == cast(E, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class F:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, F),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(F, other).i and 
                                 self.s == cast(F, other).s and 
                                 self.b == cast(F, other).b)
                )
            )
        ))
        if isinstance(other, F):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(F, other).i and 
                    self.s == cast(F, other).s and 
                    self.b == cast(F, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooF(a: F, b: F) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(F, a).i == cast(F, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class G:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, G),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(G, other).i and 
                                 self.s == cast(G, other).s and 
                                 self.b == cast(G, other).b)
                )
            )
        ))
        if isinstance(other, G):
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
    
def fooG(a: G, b: G) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(G, a).i == cast(G, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class H:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, H),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(H, other).i and 
                                 self.s == cast(H, other).s and 
                                 self.b == cast(H, other).b)
                )
            )
        ))
        if isinstance(other, H):
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
    
def fooH(a: H, b: H) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(H, a).i == cast(H, b).i
    Fold(a.state())
    Fold(b.state())
    return 0