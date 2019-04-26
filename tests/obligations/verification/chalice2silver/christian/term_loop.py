# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
This test is a ported version of
``obligations/christian/term_loop.chalice`` test from Chalice2Silver
test suite.
"""


from nagini_contracts.contracts import (
    Acc,
    Assert,
    Requires,
    Invariant,
)
from nagini_contracts.obligations import *


class A:

    def __init__(self, x: 'A', y: int) -> None:
        self.x = x
        self.y = y

    def m1(self) -> None:
        Requires(MustTerminate(1))
        x = 1
        #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
        while x < 5:
            Invariant(True)
            x += 1

    def m2(self) -> None:
        Requires(MustTerminate(1))
        x = 1
        while x < 5:
            Invariant(MustTerminate(10-x))
            x += 1

    def nested1(self) -> None:
        Requires(MustTerminate(1))
        x = 1
        y = 1
        while x < 5:
            Invariant(MustTerminate(10-x))
            x += 1
            #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
            while y < 5:
                Invariant(True)
                y += 1

    def nested2(self) -> None:
        Requires(MustTerminate(1))
        x = 1
        y = 1
        while x < 5:
            Invariant(MustTerminate(10-x))
            x += 1
            while y < 5:
                Invariant(MustTerminate(20-y))
                y += 1

    def nested3(self) -> None:
        x = 1
        y = 2
        while x < 5:
            Invariant(MustTerminate(10-x))
            x += 1
            #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
            while y < 5:
                Invariant(True)
                y += 1

    def nested4(self) -> None:
        x = 1
        y = 2
        while x < 5:
            Invariant(MustTerminate(10-x))
            x += 1
            while y < 5:
                Invariant(MustTerminate(10-y))
                y += 1

    def nested5(self) -> None:
        x = 1
        y = 2
        while x < 5:
            x += 1
            while y < 5:
                Invariant(MustTerminate(10-y))
                y += 1
