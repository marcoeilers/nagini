# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def func(i: int) -> bool:
    return i == 0

def client() -> int:
    #:: ExpectedOutput(invalid.program:invalid.let)
    Ensures(Let(Result(), bool, func))
    return 0