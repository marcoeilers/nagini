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

def test_bytearray_constr_list_bounds_low() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    a = bytearray([-1,3,4])
    
def test_bytearray_constr_list_bounds_high() -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    a = bytearray([0,3,256])

def test_bytearray_constr_bytearray() -> None:
    a = bytearray([2,3,4])
    b = bytearray(a)
    
    assert len(b) == 3
    assert b[0] == 2
    assert b[1] == 3
    assert b[2] == 4
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert 5 in b

def test_bytearray_bool() -> None:
    a = bytearray([0])
    b = bytearray(3)
    c = bytearray()
    
    assert a
    assert b
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c

def test_bytearray_eq1() -> None:
    a = bytearray([1,2,3])
    b = bytearray([1,2,3])
    
    assert a == b
    
def test_bytearray_eq2() -> None:
    a = bytearray([1,2,3])
    b = bytearray([2,2,3])
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a == b
    
def test_bytearray_eq_client1(b1: bytearray, b2: bytearray) -> None:
    Requires(bytearray_pred(b1))
    Requires(bytearray_pred(b2))
    Requires(b1 == b2)
    Requires(len(b1) > 0)
    
    assert b1[0] == b2[0]
    
def test_bytearray_eq_client2(b1: bytearray, b2: bytearray) -> None:
    Requires(bytearray_pred(b1))
    Requires(bytearray_pred(b2))
    Requires(b1 == b2)
    Requires(len(b1) > 0)
    
    b1[0] = 42
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b1[0] == b2[0]

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

def test_bytearray_append_bounds_low() -> None:
    a = bytearray()
    #:: ExpectedOutput(call.precondition:assertion.false)
    a.append(-10)

def test_bytearray_append_bounds_high() -> None:
    a = bytearray()
    #:: ExpectedOutput(call.precondition:assertion.false)
    a.append(256)

def test_bytearray_setitem() -> None:
    a = bytearray([2,3,4])
    
    a[0] = 10
    a[1] = 0
    a[2] = 255
    assert a[0] == 10
    assert a[1] == 0
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a[2] == 254

def test_bytearray_setitem_bounds_low() -> None:
    a = bytearray([0,128,255])
    #:: ExpectedOutput(call.precondition:assertion.false)
    a[0] = -1

def test_bytearray_setitem_bounds_high() -> None:
    a = bytearray([0,128,255])  
    #:: ExpectedOutput(call.precondition:assertion.false)
    a[0] = 256

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
    
def test_bytearray_getitem_slice() -> None:
    a = bytearray([2,3,4])
    b = a[1:]
    
    assert len(b) == 2
    assert b[0] == 3
    assert b[1] == 4
    
    c = a[:-1]
    assert len(c) == 2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c[0] == 3
    

def test_bytearray_perm(b: bytearray) -> None:
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    b.append(6)

def test_bytearray_bounds_low(b: bytearray) -> None:
    Requires(bytearray_pred(b))
    Requires(len(b) > 1)
    
    assert b[0] >= 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[1] < 0
    
def test_bytearray_bounds_high(b: bytearray) -> None:
    Requires(bytearray_pred(b))
    Requires(len(b) > 1)
    
    assert b[0] <= 255
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[1] > 255
    
def test_bytearray_iter_bounds(b: bytearray) -> None:
    Requires(bytearray_pred(b))
    
    for byte in b:
        assert 0 <= byte and byte < 256

def test_bytearray_hex(b: bytearray) -> None:
    Requires(bytearray_pred(b))
    
    value = b.hex()
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert value == ""