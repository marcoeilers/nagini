# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List

from nagini_contracts.contracts import *


def total(data: bytes) -> int:
    Ensures(Result() >= 0)
    s = 0
    for byte in data:
        Invariant(s >= 0)
        assert 0 <= byte and byte < 256
        s += byte
    return s


def bounded(data: bytes, i: int) -> None:
    Requires(0 <= i and i < len(data))
    assert 0 <= data[i] and data[i] < 256
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert data[i] < 255


def visited(data: bytes) -> None:
    n = 0
    for byte in data:
        Invariant(n == len(Previous(byte)))
        n += 1
    assert n == len(data)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert n == len(data) + 1


def from_list() -> None:
    xs = [0x11, 0xDA, 7]
    b = bytes(xs)
    assert len(b) == 3
    assert b[1] == 0xDA
    assert b == b"\x11\xda\x07"
    assert len(xs) == 3
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[2] == 8


def from_list_bounds(xs: List[int]) -> bytes:
    Requires(Acc(list_pred(xs)))
    #:: ExpectedOutput(call.precondition:assertion.false)
    return bytes(xs)


def from_bytearray() -> None:
    a = bytearray(3)
    a[0] = 7
    b = bytes(a)
    a[1] = 9
    assert len(b) == 3
    assert b[0] == 7
    assert b[1] == 0
    assert b == b"\x07\x00\x00"
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b[1] == 9


def from_int() -> None:
    b = bytes(2)
    assert b == b"\x00\x00"
    c = bytes()
    assert len(c) == 0
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(b) == 3


def from_int_negative(n: int) -> bytes:
    #:: ExpectedOutput(call.precondition:assertion.false)
    return bytes(n)


def from_bytes(d: bytes) -> None:
    b = bytes(d)
    assert b == d
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(b) == len(d) + 1


def built(header: bytes, value: int) -> bytes:
    Requires(0 <= value and value < 256)
    Ensures(len(Result()) == len(header) + 1)
    Ensures(Result()[len(header)] == value)
    return header + bytes([value])


def bytearray_negative(n: int) -> None:
    Requires(n < 0)
    #:: ExpectedOutput(call.precondition:assertion.false)
    a = bytearray(n)
    assert False
