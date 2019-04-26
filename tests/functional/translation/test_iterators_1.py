# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def list_loop() -> None:
    b = [1, 2, 3]
    a = [b, [4, 5]]
    for c in a:
        #:: ExpectedOutput(invalid.program:invalid.previous)
        Invariant(len(Previous(b)) > 2)
        c.append(7)
    a.append([4])