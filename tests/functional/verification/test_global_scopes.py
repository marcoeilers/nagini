# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

a, d = 2, 5
b = [a]


def foo_1() -> int:
    Requires(Acc(a) and Acc(b) and a >= 1)
    global b, a
    tmp = a
    a = 0  # b[0]
    b = [34]
    return a


def foo_2() -> int:
    global b, a
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    tmp = a
    a = 0  # b[0]
    b = [34]
    return a


def foo_3() -> int:
    #:: ExpectedOutput(expression.undefined:undefined.local.variable)
    tmp = a  # noqa: F823
    a = 0  # b[0]
    b = [34]
    return a

