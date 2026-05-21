# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f() -> None:
    #:: ExpectedOutput(unsupported:with block may only have one item)
    with open('a') as a, open('b') as b:
        pass
