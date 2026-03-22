# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from enum import IntEnum

class flag(IntEnum):
    success = 0
    failure = 1
    
class flag2(IntEnum):
    success = 0
    failure = 2

def test_value() -> None:
    f = flag(1)
    
    assert f == flag(1)
    assert f == 1
    assert f == flag.failure

    assert flag.success == 0
    assert flag.success == flag(0)
    assert flag.success == False
    assert flag2(0) == flag(0)

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert flag.success == flag.failure

def test_comparison() -> None:
    f0 = flag(0)
    f1 = flag(0)
    f2 = flag2(0)
    
    assert f0 == f1
    assert f0 is f1

    assert f1 == f2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert f1 is f2

def test_value3() -> None:
    assert flag.success == flag2.success

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert flag.failure == flag2.failure

def test_contraints(f: flag) -> None:
    assert 0 <= f
    assert f <= 1

    assert 0 <= int(f)
    assert int(f) <= 1

def test_contraints2(f: flag2) -> None:
    assert f == 0 or f == 2

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert f == 0

def test_contraints3(f: flag2) -> None:
    assert f != 1

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert f == 3

def test_precond(f: flag) -> None:
    Requires(f == flag.success)

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert f == 1