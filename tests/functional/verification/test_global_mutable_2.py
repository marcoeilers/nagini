# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


a2 = 2

@Predicate
def a2_perm() -> bool:
    return Acc(a2, 1/2)

@Pure
def get_a2() -> int:
    Requires(a2_perm())
    return Unfolding(a2_perm(), a2)

def foo_4() -> int:
    Requires(Acc(a2, 1/2))
    Requires(a2_perm() and get_a2() <= 2)
    Ensures(a2_perm())
    Ensures(Acc(a2, 1/2) and a2 == Old(a2) + 1)
    global a2
    Unfold(a2_perm())
    a2 += 1
    Fold(a2_perm())
    return a2

Fold(a2_perm())
foo_4()

#:: ExpectedOutput(call.precondition:assertion.false)
foo_4()