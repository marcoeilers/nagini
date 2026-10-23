# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f() -> None:
    t = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    #:: ExpectedOutput(unsupported:Tuples longer than 9 elements are only supported with a single element type.)
    u = (1, 2, 3, 4, 5, 6, 7, 8, 9, 'ten')
