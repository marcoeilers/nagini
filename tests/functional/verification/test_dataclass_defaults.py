# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from enum import IntEnum
from typing import List
from nagini_contracts.contracts import *
from dataclasses import dataclass, field

@dataclass(frozen=True)
class A:
    num: int = 2
    num2: int = 10
    
@dataclass(frozen=True)
class B:
    num: int
    my_field: int = 5

@dataclass(frozen=True)
class FieldClass:
    arr: List[int] = field(default_factory=list)

@dataclass(frozen=True)
class ComplexClass:
    num1: int
    num2: int = 3
    arr: List[int] = field(default_factory=list)
    arr2: List[int] = field(default_factory=list)

class Color_Enum(IntEnum):
    red = 0
    green = 1
    blue = 2
    yellow = 3

@dataclass(frozen=True)
class C:
    color: Color_Enum = Color_Enum.green

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

def test_default_factory_list1() -> None:
    a = FieldClass()
    b = FieldClass()

    a.arr.append(1)
    assert len(a.arr) == 1
    assert len(b.arr) == 0

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.arr == b.arr

def test_default_factory_list2() -> None:
    l = [1,2,3]
    a = FieldClass(l)
    b = FieldClass(l)

    a.arr.append(1)
    assert len(a.arr) == 4
    assert len(b.arr) == 4

    assert a.arr is b.arr

def test_default_factory_list3() -> None:
    a = ComplexClass(7)
    b = ComplexClass(5, arr=[1])

    assert a.num1 == 7
    assert b.num1 == 5

    assert a.num2 == 3
    assert b.num2 == 3

    a.arr.append(1)
    assert len(a.arr) == 1
    assert len(b.arr) == 1

    assert a.arr[0] == b.arr[0]

    assert len(a.arr2) == 0
    assert len(b.arr2) == 0

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.arr is b.arr

def test_default_val_enum() -> None:
    c = C()

    assert c.color == Color_Enum.green
    
    c2 = C(Color_Enum.yellow)
    assert c2.color == Color_Enum.yellow

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c.color == c2.color