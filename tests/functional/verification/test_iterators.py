#:: IgnoreFile(38)
from py2viper_contracts.contracts import *


def list_loop() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
        c.append(7)
    a.append([4])


def list_no_false() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(False)
        c.append(7)
    a.append([4])


def list_concurrent_modification() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
        c.append(7)
        #:: ExpectedOutput(call.precondition:insufficient.permission)
        a.append([4])


def list_previous() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    to_fill = []  # type: List[List[int]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
        Invariant(Acc(list_pred(to_fill)))
        Invariant(len(to_fill) == len(Previous(c)))
        c.append(7)
        to_fill.append(c)
    a.append([4])


def list_previous_2() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    to_fill = []  # type: List[List[int]]
    for c in a:
        Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
        Invariant(Acc(list_pred(to_fill)))
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(len(to_fill) == len(Previous(c)))
        c.append(7)
        to_fill.append(c)
        to_fill.append(c)
    a.append([4])


#TODO: I cannot get this to work in either Carbon or Silicon
# def list_modification(a: List[List[int]]) -> None:
#     Requires(Acc(list_pred(a)))
#     Requires(Forall(a, lambda x: (Acc(list_pred(x)), [])))
#     Ensures(Acc(list_pred(a)))
#     Ensures(Forall(a, lambda x: (Acc(list_pred(x)), []))
#             and Forall(a, lambda x: (len(x) == Old(len(x)) + 1, [])))
#     for c in a:
#         Invariant(Forall(a, lambda l: (Acc(list_pred(l)), [])))
#         Invariant(Forall(Previous(c), lambda y: (y in a, [])))
#         Invariant(Forall(Previous(c), lambda y: (len(y) > Old(len(y)), [])))
#         c.append(7)


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
