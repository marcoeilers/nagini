# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def w(normal: int, *args: int, other: bool, **kwargs: bool) -> int:
    Requires(normal == 23)
    Requires(len(args) == 2)
    Requires(args[1] == 17)
    Requires(other == True)
    Requires(len(kwargs) == 1)
    Requires('kw' in kwargs and kwargs['kw'] is False)
    Ensures(Result() == args[0])
    return args[0]


def caller() -> int:
    Ensures(Result() == 5)
    return w(23, 5, 17, kw=False, other=True)


def caller2() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    w(24, 5, 17, kw=False, other=True)


def caller3() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    w(23, 5, 17, 34, kw=False, other=True)


def caller4() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    w(23, 17, 5, kw=False, other=True)


def caller5() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    w(23, 5, 17, kw=False, other=False)


def caller6() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    w(23, 5, 17, kw=False, other=True, kw2=False)


def caller7() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    w(23, 5, 17, kw=True, other=True)


def caller8() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 7)
    return w(23, 5, 17, kw=False, other=True)
