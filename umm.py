# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


def foo1() -> None:
    Requires(MustTerminate(1))
    return

def foo2() -> None:
    return

def bar() -> None:
    Requires(MustTerminate(2))
    start = 4
    foo1()
    end = 5
    foo2()