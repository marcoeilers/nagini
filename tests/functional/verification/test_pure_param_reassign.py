# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Optional
from nagini_contracts.contracts import *


@Pure
def pick(x: Optional[int], d: int) -> int:
    Ensures(Implies(x is not None, Result() == x))
    Ensures(Implies(x is None, Result() == d))
    if x is None:
        x = d
    return x


@Pure
def bump(x: int, b: bool) -> int:
    Ensures(Result() == (x + 1 if b else x))
    if b:
        x = x + 1
    return x


@Pure
def twice(x: int, b: bool) -> int:
    Ensures(Result() == (x + 2 if b else x + 1))
    x = x + 1
    if b:
        x = x + 1
    return x


@Pure
def wrong(x: int, b: bool) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == x + 1)
    if b:
        x = x + 1
    return x
