# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# TODO: There is a problem with accessing values in the loop, I can't seem to
# do it properly.
def dict_concurrent_modification() -> None:
    b = {1: 1, 2: 2, 3: 3}
    d = {4 : 8, 5 : 9}
    a = {6: b, 7: d}
    for c in a:
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        a[54] = {5: 7}


def dict_no_false() -> None:
    b = {1: 1, 2: 2, 3: 3}
    d = {4 : 8, 5 : 9}
    a = {6: b, 7: d}
    for c in a:
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(False)


def dict_previous() -> None:
    b = {1: 1, 2: 2, 3: 3}
    a = {6: b, 7: {4: 8, 5: 9}}
    to_fill = []  # type: List[Dict[int, int]]
    for c in a:
        Invariant(Acc(list_pred(to_fill)))
        Invariant(len(to_fill) == len(Previous(c)))
        to_fill.append(a[c])


def dict_previous_2() -> None:
    b = {1: 1, 2: 2, 3: 3}
    a = {6: b, 7: {4: 8, 5: 9}}
    to_fill = []  # type: List[Dict[int, int]]
    for c in a:
        Invariant(Acc(list_pred(to_fill)))
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(len(to_fill) == len(Previous(c)))
        to_fill.append(a[c])
        to_fill.append(a[c])