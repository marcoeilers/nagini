# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast, List


class A:
    pass


def m() -> None:
    t = (1, [4, 12], 'asd', A())
    d, (g, h), *e = t
    assert d == 1
    assert len(e) == 2
    assert e[0] == 'asd'
    assert g == 4
    assert h == 12
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert e[1] == 'asd'


def m3_fail_1() -> None:
    l1 = [1]  # type: List[object]
    l2 = [4, 12, 15]  # type: List[object]
    l3 = ['asd']  # type: List[object]
    l4 = [A()]  # type: List[object]
    t = [l1, l2, l3, l4]
    #:: ExpectedOutput(assert.failed:assertion.false)
    d, (g, h), *e, z = t
    assert d[0] == 1
    assert len(e) == 1
    assert e[0][0] is 'asd'
    assert g == 4
    assert h == 12
    assert isinstance(e[0], tuple)


def m3_fail_2() -> None:
    l1: List[object] = [1]
    l2 = [4]  # type: List[object]
    l3 = ['asd']  # type: List[object]
    l4 = [A()]  # type: List[object]
    t = [l1, l2, l3, l4]
    #:: ExpectedOutput(assert.failed:assertion.false)
    d, (g, h), *e, z = t
    assert d[0] == 1
    assert len(e) == 1
    assert e[0][0] is 'asd'
    assert g == 4
    assert h == 12
    assert isinstance(e[0], tuple)


def m3_fail_3() -> None:
    l1 = [1]  # type: List[object]
    l2 = [4, 12]  # type: List[object]
    l3 = ['asd']  # type: List[object]
    l4 = [A()]  # type: List[object]
    t = [l1, l2, l3]
    # The starred receiver absorbs no elements: z gets t[2].
    d, (g, h), *e, z = t
    assert d[0] == 1
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(e) == 1
    assert e[0][0] is 'asd'
    assert g == 4
    assert h == 12
    assert isinstance(e[0], tuple)


def m3() -> None:
    l1 = [1]  # type: List[object]
    l2 = [4, 12]  # type: List[object]
    l3 = ['asd']  # type: List[object]
    l4 = [A()]  # type: List[object]
    t = [l1, l2, l3, l4]
    d, (g, h), *e, z = t
    assert d[0] == 1
    assert len(e) == 1
    assert e[0][0] is 'asd'
    assert g == 4
    assert h == 12
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(e[0], tuple)


def m4() -> None:
    hlpr = ("asd", A(), 'asd2', 34)
    a = [hlpr]
    for b, *c in a:
        Invariant(Forall(a, lambda e: (e is hlpr, [])))
        assert b is 'asd'
        assert len(c) == 3
        assert isinstance(c[0], A)
        assert cast(int, c[2]) > 20
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert cast(int, c[2]) > 50


def m5() -> None:
    a = [("asd", 'after')]
    tmp: List[str] = ['before']
    for b, *c in a:
        Invariant(Acc(list_pred(tmp)))
        tmpln = len(tmp)
        cln: int = len(c)
        tmp.append('inside')
        assert len(tmp) == tmpln + 1
        assert len(c) == cln
    assert len(b) == 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b == 'not'


def helper(l: List[int]) -> List[int]:
    Requires(Acc(list_pred(l), 2/3))
    Ensures(Result() is l)
    return l


def m6() -> None:
    l = [1, 2]
    a = b = helper(l)
    assert l is a
    assert b is l
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def m7() -> None:
    a, b, c, d = e, *f = (1, [4, 12], 'asd', A())
    assert a == e
    assert b is f[0]
    assert d is f[2]
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c is f[0]

def swap_locals() -> None:
    a = 1
    b = 2
    a, b = b, a
    assert a == 2
    assert b == 1
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b == 2


def swap_subscripts(xs: List[int]) -> None:
    Requires(list_pred(xs))
    Requires(len(xs) >= 2)
    Ensures(list_pred(xs))
    Ensures(len(xs) == Old(len(xs)))
    Ensures(xs[0] == Old(xs[1]) and xs[1] == Old(xs[0]))
    xs[0], xs[1] = xs[1], xs[0]


def rotate_subscripts(xs: List[int]) -> None:
    Requires(list_pred(xs))
    Requires(len(xs) > 2)
    Ensures(list_pred(xs))
    Ensures(len(xs) == Old(len(xs)))
    Ensures(xs[0] == Old(xs[2]) and xs[1] == Old(xs[0]) and xs[2] == Old(xs[1]))
    xs[0], xs[1], xs[2] = xs[2], xs[0], xs[1]


def starred_tail() -> None:
    a, *b, c = (1, 2, 3, 4)
    assert a == 1
    assert c == 4
    assert len(b) == 2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c == 3
