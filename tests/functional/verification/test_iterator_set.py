# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def set_loop() -> None:
    b = {1, 2, 3}
    a = {b, {4, 5}}
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(set_pred(l)), [])))
        c.add(7)
    a.add({4})


def set_no_false() -> None:
    b = {1, 2, 3}
    a = {b, {4, 5}}
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(set_pred(l)), [])))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(False)
        c.add(7)
    a.add({4})


def set_concurrent_modification() -> None:
    b = {1, 2, 3}
    a = {b, {4, 5}}
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(set_pred(l)), [])))
        c.add(7)
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        a.add({4})


def set_previous() -> None:
    b = {1, 2, 3}
    a = {b, {4, 5}}
    to_fill = []  # type: List[Set[int]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(set_pred(l)), [])))
        Invariant(Acc(list_pred(to_fill)))
        Invariant(len(to_fill) == len(Previous(c)))
        c.add(7)
        to_fill.append(c)


def set_previous_2() -> None:
    b = {1, 2, 3}
    a = {b, {4, 5}}
    to_fill = []  # type: List[Set[int]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(set_pred(l)), [])))
        Invariant(Acc(list_pred(to_fill)))
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(len(to_fill) == len(Previous(c)))
        c.add(7)
        to_fill.append(c)
        to_fill.append(c)