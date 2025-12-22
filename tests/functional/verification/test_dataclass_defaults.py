# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from dataclasses import dataclass

@dataclass(frozen=True)
class A:
    num: int = 2
    num2: int = 10
    
@dataclass(frozen=True)
class B:
    num: int
    my_field: int = 5
    
def test_default_vals1() -> None:
    a = A()
    
    assert a.num == 2
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.num == 3
    
def test_default_vals2(val: int) -> None:
    b = B(val)
    
    assert b.num == val
    assert b.my_field == 5
    
    b2 = B(val, val)
    assert b2.num == b2.my_field
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b2.my_field == 5