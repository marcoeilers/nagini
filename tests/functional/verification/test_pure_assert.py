# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

@Pure
def testing1(i1: int, i2: int) -> int:
    Ensures(Result() >= i1 and Result() >= i2)
    if i1 > i2:
        Assert(i1 >= i2)
        return i1
    return i2


@Pure  #:: ExpectedOutput(function.not.wellformed:assertion.false)
def testing2(i1: int, i2: int) -> int:
    Ensures(Result() >= i1 and Result() >= i2)
    if i1 > i2:
        Assert(i1 == i2)
        return i1
    return i2

@Pure
def testing3(i1: int, i2: int) -> int:
    Ensures(Result() >= i1 and Result() >= i2)
    if i1 > i2:
        return i1
    Assert(i1 <= i2)
    return i2

@Pure  #:: ExpectedOutput(function.not.wellformed:assertion.false)
def testing4(i1: int, i2: int) -> int:
    Ensures(Result() >= i1 and Result() >= i2)
    if i1 > i2:
        return i1
    Assert(i1 == i2)
    return i2