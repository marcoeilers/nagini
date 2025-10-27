# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def set_bit() -> None:
    a = PByteSeq.int_set_bit(0, 7, True)
    assert a == 128

    a = PByteSeq.int_set_bit(a, 6, True)
    assert a == 192

    a = PByteSeq.int_set_bit(a, 7, False)
    assert a == 64

    a = PByteSeq.int_set_bit(a, 0, True)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a == 64

def get_bit1() -> None:
    a = 255
    assert PByteSeq.int_get_bit(a, 0)
    assert PByteSeq.int_get_bit(a, 1)
    assert PByteSeq.int_get_bit(a, 2)
    assert PByteSeq.int_get_bit(a, 3)
    assert PByteSeq.int_get_bit(a, 4)
    assert PByteSeq.int_get_bit(a, 5)
    assert PByteSeq.int_get_bit(a, 6)
    assert PByteSeq.int_get_bit(a, 7)

def get_bit2(pos: int) -> None:
    Requires(0 <= pos and pos < 8)
    a = 15

    if pos < 4:
        assert PByteSeq.int_get_bit(a, pos)
    else:
        #:: ExpectedOutput(assert.failed:assertion.false)
        assert PByteSeq.int_get_bit(a, 4)

def set_get_bit(val: int, pos: int, bit: bool) -> None:
    Requires(0 <= val and val <= 255)
    Requires(0 <= pos and pos < 8)

    mod_val = PByteSeq.int_set_bit(val, pos, bit)
    assert PByteSeq.int_get_bit(mod_val, pos) == bit