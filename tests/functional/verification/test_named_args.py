# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


class Whatever:

    def something(self, normal: int, named1: bool, named2: object,
                  named_default: int = 13,
                  named_default2: Tuple[int, bool]=(2, True)) -> int:
        Ensures(Result() == named_default2[0])
        return named_default2[0]

    @Pure
    def something_func(self, normal: int, named1: bool, named2: object,
                       named_default: int = 13,
                       named_default2: Tuple[int, bool]=(2, True)) -> int:
        Ensures(Result() == named_default2[0])
        return named_default2[0]


def something(normal: int, named1: bool, named2: object,
              named_default: int = 13,
              named_default2: Tuple[int, bool]=(2, True)) -> int:
    Ensures(Result() == named_default2[0])
    return named_default2[0]


@Pure
def something_func(normal: int, named1: bool, named2: object,
                   named_default: int = 13,
                   named_default2: Tuple[int, bool]=(2, True)) -> int:
    Ensures(Result() == named_default2[0])
    return named_default2[0]


def caller() -> int:
    Ensures(Result() == 12)
    r = something(23, False, named_default2=(12, False), named2=Whatever())
    return r


def caller2() -> int:
    Ensures(Result() == 24)
    w = Whatever()
    r = w.something(23, False, named_default2=(24, False), named2=Whatever())
    return r


def caller3() -> int:
    Ensures(Result() == 36)
    w = Whatever()
    r = Whatever.something(w, 23, False, named_default2=(36, False),
                           named2=Whatever())
    return r


def caller4() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 11)
    r = something(23, False, named_default2=(12, False), named2=Whatever())
    return r


def caller5() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 23)
    w = Whatever()
    r = w.something(23, False, named_default2=(24, False), named2=Whatever())
    return r


def caller6() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 35)
    w = Whatever()
    r = Whatever.something(w, 23, False, named_default2=(36, False),
                           named2=Whatever())
    return r


def caller_func() -> int:
    Ensures(Result() == 12)
    r = something_func(23, False, named_default2=(12, False), named2=Whatever())
    return r


def caller2_func() -> int:
    Ensures(Result() == 24)
    w = Whatever()
    r = w.something_func(23, False, named_default2=(24, False),
                         named2=Whatever())
    return r


def caller3_func() -> int:
    Ensures(Result() == 36)
    w = Whatever()
    r = Whatever.something_func(w, 23, False, named_default2=(36, False),
                                named2=Whatever())
    return r


def caller4_func() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 11)
    r = something_func(23, False, named_default2=(12, False),
                       named2=Whatever())
    return r


def caller5_func() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 23)
    w = Whatever()
    r = w.something_func(23, False, named_default2=(24, False),
                         named2=Whatever())
    return r


def caller6_func() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 35)
    w = Whatever()
    r = Whatever.something_func(w, 23, False, named_default2=(36, False),
                                named2=Whatever())
    return r
