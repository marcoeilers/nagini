# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from types import EllipsisType


def fun() -> bool:
    assert --(... == ...)++(Ellipsis == ...) == 2
    return True


def fun_fail() -> bool:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert --(... == ...)++(... == ...) == 3
    return True


def fun2() -> bool:
    assert --(... is ...)++(... is ...) == 2
    return True


def fun2_fail() -> bool:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert --(... is ...)++(... is ...) == 3
    return True


def other() -> None:
    assert ... == Ellipsis
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def single(e: EllipsisType) -> None:
    assert e is ...
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def single2(e: EllipsisType) -> None:
    assert e == ...
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def type_check() -> None:
    assert isinstance(..., EllipsisType)
    assert type(...) == EllipsisType


def type_check2() -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert type(...) != EllipsisType


def type_check3() -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert not isinstance(..., EllipsisType)

