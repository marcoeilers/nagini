# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import cast



def and_1(a: bool, b: bool, c: object) -> None:
    anded = a & b
    Assert(anded == b & a)
    if not a:
        Assert(not anded)
    if anded:
        Assert(b)
    if isinstance(c, bool):
        other = cast(bool, c) & a
        if other:
            Assert(cast(bool, c))

def and_2(a: bool, b: bool, c: object) -> None:
    anded = a & b
    if not anded:
        Assert(not a or not b)
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(not a)


def or_1(a: bool, b: bool, c: object) -> None:
    ored = a | b
    Assert(ored == b | a)
    if a:
        Assert(ored)
    if not ored:
        Assert(not b)
    if isinstance(c, bool):
        other = cast(bool, c) | a
        if not other:
            Assert(not cast(bool, c))


def or_2(a: bool, b: bool, c: object) -> None:
    ored = a | b
    if ored:
        Assert(not (not a and not b))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(a)


def xor_1(a: bool, b: bool, c: object) -> None:
    xored = a ^ b
    Assert(xored == b ^ a)
    if not a:
        Assert(xored or not b)
    if xored and a:
        Assert(not b)
    if isinstance(c, bool):
        other = cast(bool, c) ^ a
        if other ^ a:
            Assert(cast(bool, c))

def xor_2(a: bool, b: bool, c: object) -> None:
    xored = a ^ b
    if not xored:
        Assert(a == b)
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(a and b)


def and_3(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c > -128 and c < 127)
    intbool = a & b
    boolint = b & a
    intint = a & c
    Assert(intbool == boolint)
    if isinstance(a, bool):
        Assert(intbool == (cast(bool, a) and b))
    if a == 3:
        if c == 17:
            Assert(intint == 1)
        if c == 19:
            Assert(intint == 3)
        if c == 16:
            #:: ExpectedOutput(assert.failed:assertion.false)
            Assert(intint == 1)

def and_3a(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c > -128 and c < 127)
    intbool = a & b
    boolint = b & a
    if a == 5:
        Assert(intbool == (1 if b else 0))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(intbool == 1)

def and_4(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c > -130 and c < 127)
    #:: ExpectedOutput(application.precondition:assertion.false)
    intint = a & c


def or_3(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c > -128 and c < 127)
    intbool = a | b
    boolint = b | a
    intint = a | c
    Assert(intbool == boolint)
    if isinstance(a, bool):
        Assert(intbool == (cast(bool, a) or b))

    if a == 3:
        if c == 17:
            Assert(intint == 19)
        if c == 19:
            Assert(intint == 19)
        if c == 16:
            #:: ExpectedOutput(assert.failed:assertion.false)
            Assert(intint == 1)

def or_3a(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c > -128 and c < 127)
    intbool = a | b
    boolint = b | a
    if a == 4:
        Assert(intbool == (5 if b else 4))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(intbool == 5)

def or_4(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c > -130 and c < 127)
    #:: ExpectedOutput(application.precondition:assertion.false)
    intint = a | c


def xor_3(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c >= -128 and c <= 127)
    intbool = a ^ b
    boolint = b ^ a
    intint = a ^ c
    Assert(intbool == boolint)
    if isinstance(a, bool):
        Assert(intbool == (cast(bool, a) != b))

    if a == 3:
        if c == 17:
            Assert(intint == 18)
        if c == 19:
            Assert(intint == 16)
        if c == 16:
            #:: ExpectedOutput(assert.failed:assertion.false)
            Assert(intint == 16)

def xor_3a(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c >= -128 and c <= 127)
    intbool = a ^ b
    boolint = b ^ a
    if a == 5:
        Assert(intbool == (4 if b else 5))
        #:: ExpectedOutput(assert.failed:assertion.false)
        Assert(intbool == 5)

def xor_4(a: int, b: bool, c: int) -> None:
    Requires(a > -100 and a < 100)
    Requires(c >= -128 and c < 129)
    #:: ExpectedOutput(application.precondition:assertion.false)
    intint = a ^ c