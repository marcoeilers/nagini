# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def fun() -> bool:
    assert --(... == ...)++(... == ...) == 2
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


def single(e: ellipsis) -> None:
    assert e is ...
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False

def single2(e: ellipsis) -> None:
    assert e == ...
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False

