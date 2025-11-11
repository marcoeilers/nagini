from nagini_contracts.contracts import *

@Opaque
@Pure
def positive1(i1: int) -> bool:
    return i1 > 0

@Opaque
@Pure
def positive2(i1: PInt) -> bool:
    return i1 > 0

def client1(i1: int, i2: int) -> None:
    if i1 == i2:
        if positive1(i1):
            #:: ExpectedOutput(assert.failed:assertion.false)
            Assert(positive1(i2))

def client2(i1: int, i2: int) -> None:
    if i1 == i2:
        if positive2(i1):
            Assert(positive2(i2))


@Opaque
@Pure
def true1(i1: bool) -> bool:
    return i1

@Opaque
@Pure
def true2(i1: PBool) -> bool:
    return i1


def bclient1(i1: bool, i2: bool) -> None:
    if i1 == i2:
        if true1(i1):
            Assert(true1(i2))

def bclient2(i1: bool, i2: bool) -> None:
    if i1 == i2:
        if true2(i1):
            Assert(true2(i2))