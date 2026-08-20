# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f() -> None:
    #:: ExpectedOutput(unsupported:Tuples longer than 9 elements are currently unsupported. Please file an issue to resolve this.)
    t = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
