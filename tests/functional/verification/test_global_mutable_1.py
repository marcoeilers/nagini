# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


a1 = 1


a1 += 1


def foo_1() -> int:
    Requires(Acc(a1) and a1 >= 1)
    global a1
    a1 += 1
    return a1


def foo_2() -> int:
    Requires(Acc(a1) and a1 >= 1)
    Ensures(Acc(a1) and a1 == Old(a1) + 1)
    global a1
    a1 += 1
    return a1





foo_2()
assert a1 == 3
foo_2()
assert a1 == 4
foo_1()

#:: ExpectedOutput(call.precondition:insufficient.permission)
foo_1()