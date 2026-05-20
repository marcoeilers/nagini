# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f() -> None:
    #:: ExpectedOutput(unsupported:range() step is currently not supported.)
    for i in range(0, 10, 2):
        pass
