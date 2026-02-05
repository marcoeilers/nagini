# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def test_seq() -> None:
    no_ints = PByteSeq()
    assert len(no_ints) == 0
    ints = PByteSeq(1, 2, 3)

    assert 3 in ints and 1 in ints
    assert 4 not in ints
    assert ints[1] == 2
    assert len(ints) == 3
    ints2 = ints + ints
    assert len(ints2) == 6
    assert ints2[3] == 1
    ints3 = ints2.take(4)
    assert len(ints3) == 4
    assert ints3[1] == ints2[1]
    ints4 = ints.update(0, 3)
    assert 1 not in ints4
    assert ints4[0] == 3
    ints5 = ints.drop(2)
    assert len(ints5) == 1
    assert ints5[0] == 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False

def test_byteseq_bounds_low(b: PByteSeq) -> None:
    Requires(len(b) > 1)
    
    assert b[0] >= 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[1] < 0
    
def test_byteseq_bounds_high(b: PByteSeq) -> None:
    Requires(len(b) > 1)
    
    assert b[0] <= 255
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[1] > 255

def test_range() -> None:
    ints = PByteSeq(1,3,5,6,8)
    r = ints.drop(1).take(2)

    assert len(ints) == 5
    assert len(r) == 2
    assert 5 in r
    assert r[0] == 3
    assert 1 not in r
    assert 8 not in r

    #:: ExpectedOutput(assert.failed:assertion.false)
    assert r[1] == 6

def test_list_ToByteSeq() -> None:
    a = [1,2,3]
    assert ToByteSeq(a) == PByteSeq(1,2,3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def test_bytearray_ToByteSeq() -> None:
    a = bytearray([1,2,3])
    assert ToByteSeq(a) == PByteSeq(1,2,3)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False
    
def test_bytearray_bounds(b_array: bytearray) -> None:
    Requires(bytearray_pred(b_array))
    Requires(len(b_array) > 2)    
    seq = ToByteSeq(b_array)
    
    assert 0 <= seq[0] and seq[0] <= 0xFF
    
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert seq[1] >= 256