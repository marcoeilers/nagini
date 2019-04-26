# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def something(s: str, a: Tuple[str, int]) -> Tuple[str, str, int]:
    Requires(a[1] > 8)
    Ensures(Result()[1] == 'asd')
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


def something_else() -> int:
    Ensures(Result() == 15)
    a, b, c = something('asd', ('assaa', 15))
    return c


def something_else_2() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 17)
    a, b, c = something('asd', ('assaa', 15))
    return c
