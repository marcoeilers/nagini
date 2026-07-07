# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import cast

from nagini_contracts.contracts import *
from dataclasses import dataclass, field

@dataclass
class A:
    data: int
    
    @Pure
    def __eq__(self, other: object) -> bool:
        Requires(Rd(self.data))
        Requires(Implies(isinstance(other, A), Rd(cast(A, other).data)))
        if not isinstance(other, A):
            return False
        
        return self.data == other.data

@dataclass
class C:
    fields: list[A]

@dataclass
class D:
    value: int
    length: int
    text: str

@dataclass
class ListClass:
    arr: list[int] = field(default_factory=list)

def test_1(val: int) -> None:
    a = A(val)
    
    assert a.data == val
    
    a.data = 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.data == val
    
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

def test_3() -> None:
    c = C([A(0)])

    assert c.fields[0].data == 0

    c.fields = []
    assert len(c.fields) == 0

def test_named_param(val: int, length: int) -> None:
    d = D(length=length, value=val, text="")

    assert d.value == val
    assert d.text == ""

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert d.length == 2

def test_eq_1(val: int) -> None:
    a1 = A(val)
    a2 = A(val)
    a3 = A(0)
    
    assert a1 == a2
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a1 == a3

def test_list_ref() -> None:
    l = [1,2,3]
    f = ListClass(l)

    l.append(4)
    assert len(f.arr) == 4
    assert ToSeq(f.arr) == PSeq(1,2,3,4)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert f.arr[0] == 5

def test_list_conditions(l: list[int]) -> None:
    Requires(list_pred(l))
    Requires(Forall(l, lambda i: 0 <= i and i < 10))

    f = ListClass(l)
    assert Forall(f.arr, lambda i: 0 <= i and i < 10)

def test_list_eq(left: ListClass, right: ListClass) -> None:
    Requires(Acc(left.arr) and list_pred(left.arr))
    Requires(Acc(right.arr) and list_pred(right.arr))
    Requires(len(left.arr) == len(right.arr))

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert left.arr == right.arr

def test_list_eq_elements(left: ListClass, right: ListClass) -> None:
    Requires(Acc(left.arr) and list_pred(left.arr))
    Requires(Acc(right.arr) and list_pred(right.arr))
    Requires(len(left.arr) == len(right.arr))
    Requires(Forall(int, lambda i: Implies(0 <= i and i < len(left.arr), left.arr[i] == right.arr[i])))

    assert left.arr == right.arr
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert left.arr is right.arr