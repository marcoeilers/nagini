# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple, Union, cast


def something(s: str, a: Tuple[str, int]) -> Tuple[str, str, int]:
    Requires(a[1] > 8)
    Ensures(ResultT(Tuple[str, str, int])[1] == 'asd')
    Ensures(Result()[2] == a[1])
    Ensures(Result()[2] > 6)
    c = s + 'asdasd'
    b = (c, a[0])
    return c, 'asd', a[1]


def something_2(s: str, a: Tuple[str, int]) -> Tuple[str, str, int]:
    Requires(a[1] > 8)
    Ensures(Result()[1] == 'asd')
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result()[2] == a[1])
    c = s + 'asdasd'
    b = (c, a[0])
    return c, 'asd', a[1] + 2


def something_3(s: int, hurgh: Tuple[int, ...]) -> None:
    Requires(len(hurgh) > 2 and hurgh[1] > 8)
    if len(hurgh) > 5:
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(hurgh[4] != s)


def something_else() -> int:
    Ensures(Result() == 15)
    a, b, c = something('asd', ('assaa', 15))
    return c


def something_else_2() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 17)
    a, b, c = something('asd', ('assaa', 15))
    return c


def tuple_union_1(t: Union[Tuple[int, ...], int]) -> int:
    assert isinstance(t, int) or isinstance(t, tuple)
    if isinstance(t, tuple):
        a: Tuple[int, ...] = cast(tuple, t)
        if len(a) > 0:
            c = a[0]
        else:
            c = 4
    else:
        c = cast(int, t)
    return c


def tuple_union_1_fail(t: Union[Tuple[int, ...], int]) -> None:
    assert isinstance(t, int) or isinstance(t, tuple)
    if isinstance(t, tuple):
        a: Tuple[int, ...] = cast(tuple, t)
        #:: ExpectedOutput(application.precondition:assertion.false)
        c = a[0]
    else:
        c = cast(int, t)


def tuple_union_2(t: Union[Tuple[int, int], int]) -> int:
    assert isinstance(t, int) or isinstance(t, tuple)
    if isinstance(t, tuple):
        a: Tuple[int, ...] = cast(tuple, t)
        c = a[0]
    else:
        c = cast(int, t)
    return c


def tuple_union_2_fail(t: Union[Tuple[int, int], int]) -> None:
    assert isinstance(t, int) or isinstance(t, tuple)
    if isinstance(t, tuple):
        a: Tuple[int, ...] = cast(tuple, t)
        #:: ExpectedOutput(application.precondition:assertion.false)
        c = a[3]
    else:
        c = cast(int, t)

def take_var_tuple(t: Tuple[int, ...]) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(t) == 1 or len(t) == 0

def take_specific_tuple(t: Tuple[int, int, int]) -> None:
    pass

def caller_1(t: Tuple[int, int], t2: Tuple[int, str]) -> None:
    take_var_tuple((1,))
    take_var_tuple(t)
    take_specific_tuple((1,2,3))
    #:: ExpectedOutput(application.precondition:assertion.false)
    umm = cast(Tuple[int, ...], t2)

