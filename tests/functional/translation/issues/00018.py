# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def foo() -> None:
    while True:
        a = True
        #:: ExpectedOutput(invalid.program:invalid.contract.position)
        Invariant(a)
