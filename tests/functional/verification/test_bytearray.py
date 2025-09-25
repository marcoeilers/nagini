# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def test_bytearray_constr() -> None:
    a = bytearray()
    assert len(a) == 0
    assert 6 not in a
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 2 in a
    
def test_bytearray_constr_int() -> None:
    a = bytearray(7)
    assert len(a) == 7
    assert a[3] == 0
    assert 6 not in a
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 2 in a
    
def test_bytearray_constr_list() -> None:
    a = bytearray([2,3,4])
    assert len(a) == 3
    assert a[0] == 2
    assert a[1] == 3
    assert a[2] == 4
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 5 in a
    
def test_bytearray_constr_bytearray() -> None:
    a = bytearray([2,3,4])
    b = bytearray(a)
    
    assert len(b) == 3
    assert b[0] == 2
    assert b[1] == 3
    assert b[2] == 4
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 5 in b
    
def test_byterray_append() -> None:
    a = bytearray([2,3,4])
    a.append(5)
    
    assert len(a) == 4
    assert a[0] == 2
    assert a[1] == 3
    assert a[2] == 4
    assert a[3] == 5
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[2] == 8
    
def test_byterray_extend() -> None:
    a = bytearray([2,3,4])
    b = bytearray([5,6,7])
    a.extend(b)
    
    assert len(a) == 6
    assert a[4] == 6
    assert a[5] == 7
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[3] == 8
    
def test_bytearray_reverse() -> None:
    a = bytearray([2,3,4])
    a.reverse()
    
    assert len(a) == 3
    assert a[0] == 4
    assert a[1] == 3
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[2] == 4