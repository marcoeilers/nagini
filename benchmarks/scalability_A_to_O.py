# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

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
class I:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, I),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(I, other).i and 
                                 self.s == cast(I, other).s and 
                                 self.b == cast(I, other).b)
                )
            )
        ))
        if isinstance(other, I):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(I, other).i and 
                    self.s == cast(I, other).s and 
                    self.b == cast(I, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooI(a: I, b: I) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(I, a).i == cast(I, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class J:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, J),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(J, other).i and 
                                 self.s == cast(J, other).s and 
                                 self.b == cast(J, other).b)
                )
            )
        ))
        if isinstance(other, J):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(J, other).i and 
                    self.s == cast(J, other).s and 
                    self.b == cast(J, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooJ(a: J, b: J) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(J, a).i == cast(J, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class K:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, K),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(K, other).i and 
                                 self.s == cast(K, other).s and 
                                 self.b == cast(K, other).b)
                )
            )
        ))
        if isinstance(other, K):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(K, other).i and 
                    self.s == cast(K, other).s and 
                    self.b == cast(K, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooK(a: K, b: K) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(K, a).i == cast(K, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class L:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, L),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(L, other).i and 
                                 self.s == cast(L, other).s and 
                                 self.b == cast(L, other).b)
                )
            )
        ))
        if isinstance(other, L):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(L, other).i and 
                    self.s == cast(L, other).s and 
                    self.b == cast(L, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooL(a: L, b: L) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(L, a).i == cast(L, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class M:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, M),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(M, other).i and 
                                 self.s == cast(M, other).s and 
                                 self.b == cast(M, other).b)
                )
            )
        ))
        if isinstance(other, M):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(M, other).i and 
                    self.s == cast(M, other).s and 
                    self.b == cast(M, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooM(a: M, b: M) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(M, a).i == cast(M, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class N:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, N),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(N, other).i and 
                                 self.s == cast(N, other).s and 
                                 self.b == cast(N, other).b)
                )
            )
        ))
        if isinstance(other, N):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(N, other).i and 
                    self.s == cast(N, other).s and 
                    self.b == cast(N, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooN(a: N, b: N) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(N, a).i == cast(N, b).i
    Fold(a.state())
    Fold(b.state())
    return 0
class O:
    def __init__(self, i: int, s: str, b: bool) -> None:
        self.i: int = i
        self.s: str = s
        self.b: bool = b

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(
            isinstance(other, O),
            Unfolding(self.state(),
                Unfolding(state_pred(other),
                    Result() == (self.i == cast(O, other).i and 
                                 self.s == cast(O, other).s and 
                                 self.b == cast(O, other).b)
                )
            )
        ))
        if isinstance(other, O):
            return Unfolding(self.state(),
                Unfolding(state_pred(other),
                    self.i == cast(O, other).i and 
                    self.s == cast(O, other).s and 
                    self.b == cast(O, other).b
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Acc(self.i) and Acc(self.s) and Acc(self.b)
    
def fooO(a: O, b: O) -> int:
    Requires(state_pred(a))
    Requires(state_pred(b))
    Unfold(a.state())
    Unfold(b.state())
    res = a == b
    if res:
        assert cast(O, a).i == cast(O, b).i
    Fold(a.state())
    Fold(b.state())
    return 0