# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from dataclasses import dataclass

@dataclass(frozen=True)
class A:
    data: int
    
    @Pure
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, A):
            return False
        
        return self.data == other.data

@dataclass(frozen=True)
class B:
    field: A

    @Pure
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, B):
            return False
        
        return self.field == other.field

@dataclass(frozen=True)
class C:
    fields: list[A]


def test_1(val: int) -> None:
    a = A(val)
    
    assert a.data == val
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.data == 2
    
def test_2() -> None:
    a1 = A(0)
    a2 = A(3)
    a3 = A(42)
    c = C([a1, a2, a3])
    
    assert len(c.fields) == 3
    assert c.fields[0].data == 0
    
    c.fields.append(A(20))
    assert len(c.fields) == 4
    assert c.fields[3].data == 20
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c.fields[1].data == c.fields[2].data
   
def test_eq_1(val: int) -> None:
    a1 = A(val)
    a2 = A(val)
    a3 = A(0)
    
    assert a1 == a2
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a1 == a3

def test_eq_2(a1: A, a2: A) -> None:
    b1 = B(a1)
    b2 = B(a1)
    b3 = B(a2)
    
    assert b1 == b2
    
    if a1 == a2:
        assert b1 == b3
    else:
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert b1 == b3