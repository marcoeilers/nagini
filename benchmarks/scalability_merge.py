# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast

class A:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, A), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(A, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, A):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(A, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class B:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, B), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(B, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, B):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(B, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class C:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, C), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(C, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, C):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(C, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class D:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, D), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(D, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, D):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(D, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class E:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, E), Unfolding(
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
        elif isinstance(other, E):
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

class F:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, F), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(F, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, F):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(F, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class G:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, G), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(G, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, G):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(G, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class H:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, H), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(H, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, H):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(H, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class I:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, I), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(I, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, I):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(I, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class J:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, J), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(J, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, J):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(J, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class K:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, K), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(K, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, K):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(K, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class L:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, L), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(L, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, L):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(L, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class M:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, M), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(M, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, M):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(M, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class N:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, N), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(N, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, N):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(N, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class O:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, O), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(O, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, O):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(O, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class P:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, P), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(P, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, P):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(P, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class Q:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Q), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(Q, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, Q):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(Q, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class R:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, R), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(R, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, R):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(R, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class S:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, S), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(S, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, S):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(S, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class T:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, T), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(T, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, T):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(T, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class U:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, U), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(U, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, U):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(U, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class V:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, V), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(V, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, V):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(V, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class W:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, W), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(W, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, W):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(W, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class X:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, X), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(X, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, X):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(X, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class Y:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Y), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(Y, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, Y):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(Y, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)

class Z:
    def __init__(self, i: int) -> None:
        self.i: int = i
        Fold(self.state())
        Ensures(self.state())

    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(Implies(self is other, Result()))
        Ensures(
            Implies(
                isinstance(other, Z), Unfolding(
                    self.state(),
                    Implies(
                        not Stateless(other), Unfolding(
                            state_pred(other),
                            Result() == (self.i == cast(Z, other).i)
                        )
                    )
                )
            )
        )
        if self is other:
            return True
        elif isinstance(other, Z):
            return Unfolding(
                self.state(),
                Unfolding(
                    state_pred(other),
                    self.i == cast(Z, other).i
                )
            )
        return False

    @Predicate
    def state(self) -> bool:
        return Wildcard(self.i)
    
def fooA(o1: object, o2: object) -> int:
    Requires(isinstance(o1, A))
    Requires(isinstance(o2, A))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(A, o1).i == cast(A, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooB(o1: object, o2: object) -> int:
    Requires(isinstance(o1, B))
    Requires(isinstance(o2, B))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(B, o1).i == cast(B, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0


def fooC(o1: object, o2: object) -> int:
    Requires(isinstance(o1, C))
    Requires(isinstance(o2, C))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(C, o1).i == cast(C, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0


def fooD(o1: object, o2: object) -> int:
    Requires(isinstance(o1, D))
    Requires(isinstance(o2, D))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(D, o1).i == cast(D, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0


def fooE(o1: object, o2: object) -> int:
    Requires(isinstance(o1, E))
    Requires(isinstance(o2, E))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(E, o1).i == cast(E, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0


def fooF(o1: object, o2: object) -> int:
    Requires(isinstance(o1, F))
    Requires(isinstance(o2, F))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(F, o1).i == cast(F, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0


def fooG(o1: object, o2: object) -> int:
    Requires(isinstance(o1, G))
    Requires(isinstance(o2, G))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(G, o1).i == cast(G, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooH(o1: object, o2: object) -> int:
    Requires(isinstance(o1, H))
    Requires(isinstance(o2, H))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(H, o1).i == cast(H, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooI(o1: object, o2: object) -> int:
    Requires(isinstance(o1, I))
    Requires(isinstance(o2, I))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(I, o1).i == cast(I, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooJ(o1: object, o2: object) -> int:
    Requires(isinstance(o1, J))
    Requires(isinstance(o2, J))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(J, o1).i == cast(J, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooK(o1: object, o2: object) -> int:
    Requires(isinstance(o1, K))
    Requires(isinstance(o2, K))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(K, o1).i == cast(K, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooL(o1: object, o2: object) -> int:
    Requires(isinstance(o1, L))
    Requires(isinstance(o2, L))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(L, o1).i == cast(L, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooM(o1: object, o2: object) -> int:
    Requires(isinstance(o1, M))
    Requires(isinstance(o2, M))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(M, o1).i == cast(M, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooN(o1: object, o2: object) -> int:
    Requires(isinstance(o1, N))
    Requires(isinstance(o2, N))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(N, o1).i == cast(N, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooO(o1: object, o2: object) -> int:
    Requires(isinstance(o1, O))
    Requires(isinstance(o2, O))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(O, o1).i == cast(O, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooP(o1: object, o2: object) -> int:
    Requires(isinstance(o1, P))
    Requires(isinstance(o2, P))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(P, o1).i == cast(P, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooQ(o1: object, o2: object) -> int:
    Requires(isinstance(o1, Q))
    Requires(isinstance(o2, Q))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(Q, o1).i == cast(Q, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooR(o1: object, o2: object) -> int:
    Requires(isinstance(o1, R))
    Requires(isinstance(o2, R))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(R, o1).i == cast(R, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooS(o1: object, o2: object) -> int:
    Requires(isinstance(o1, S))
    Requires(isinstance(o2, S))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(S, o1).i == cast(S, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooT(o1: object, o2: object) -> int:
    Requires(isinstance(o1, T))
    Requires(isinstance(o2, T))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(T, o1).i == cast(T, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooU(o1: object, o2: object) -> int:
    Requires(isinstance(o1, U))
    Requires(isinstance(o2, U))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(U, o1).i == cast(U, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooV(o1: object, o2: object) -> int:
    Requires(isinstance(o1, V))
    Requires(isinstance(o2, V))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(V, o1).i == cast(V, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooW(o1: object, o2: object) -> int:
    Requires(isinstance(o1, W))
    Requires(isinstance(o2, W))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(W, o1).i == cast(W, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooX(o1: object, o2: object) -> int:
    Requires(isinstance(o1, X))
    Requires(isinstance(o2, X))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(X, o1).i == cast(X, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooY(o1: object, o2: object) -> int:
    Requires(isinstance(o1, Y))
    Requires(isinstance(o2, Y))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(Y, o1).i == cast(Y, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0

def fooZ(o1: object, o2: object) -> int:
    Requires(isinstance(o1, Z))
    Requires(isinstance(o2, Z))
    Requires(state_pred(o1))
    Requires(state_pred(o2))
    Requires(
        Unfolding(state_pred(o1),
            Unfolding(state_pred(o2),
                cast(Z, o1).i == cast(Z, o2).i
            )
        )
    )
    Ensures(state_pred(o1))
    Ensures(state_pred(o2))
    assert o1 == o2
    return 0
