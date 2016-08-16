"""
This test is a ported version of ``obligations/termination.chalice``
test from Chalice2Silver test suite.
"""


from py2viper_contracts.contracts import (
    Assert,
    Requires,
    Invariant,
    Implies,
)
from py2viper_contracts.obligations import *


def over_in_one() -> None:
    Requires(MustTerminate(1))


def some_time() -> None:
    Requires(MustTerminate(10))


def i_time(i: int) -> None:
    Requires(i > 0)
    #:: Label(i_time__MustTerminate)
    Requires(MustTerminate(i))


def no_time() -> None:
    pass


def f1() -> None:
    Requires(MustTerminate(1))
    #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
    over_in_one()


def f2() -> None:
    Requires(MustTerminate(2))
    over_in_one()
    i_time(1)


def f3(n: int) -> None:
    Requires(n > 1)
    Requires(MustTerminate(n))
    i = 0
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
    while i < n:
        Invariant(MustTerminate(n - i))
        over_in_one()


def f3_a(n: int) -> None:
    Requires(n > 1)
    Requires(MustTerminate(n))
    i = 0
    while i < n:
        Invariant(MustTerminate(n - i))
        Invariant(i >= 0)
        over_in_one()
        if n - i - 1 > 0:
            i_time(n - i - 1)
        i += 1


def non_terminating_call() -> None:
    over_in_one()
    i_time(5)
    no_time()


def f4() -> None:
    Requires(MustTerminate(10))
    i_time(9)
    i_time(7)
    i_time(8)
    #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
    i_time(10)


def loop1() -> None:
    Requires(MustTerminate(2))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_not_promised)
    while i < n:
        pass


def loop2() -> None:
    Requires(MustTerminate(2))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
    while i < n:
        Invariant(MustTerminate(n-i+1))
        if i == 2:
            i = i - 1
        i = i + 1


def loop3() -> None:
    Requires(MustTerminate(2))
    i = 0
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        #:: ExpectedOutput(call.precondition:obligation_measure.non_positive,i_time__MustTerminate)|OptionalOutput(leak_check.failed:must_terminate.not_taken)
        i_time(i)
        i = i + 1


def loop3_a() -> None:
    Requires(MustTerminate(2))
    i = 1
    n = 10
    while i < n:
        Invariant(MustTerminate(n-i+1))
        Invariant(i > 0)
        #:: ExpectedOutput(leak_check.failed:must_terminate.not_taken)
        i_time(i)
        i = i + 1


def loop4() -> None:
    Requires(MustTerminate(2))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
    while i < n:
        Invariant(MustTerminate(1))
        i = i + 1


def hidden_obligation() -> None:
    Requires(MustTerminate(2))
    i = 0
    n = 10
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_not_promised)
    while i < n:
        Invariant(Implies(i > n, MustTerminate(n-i)))
        i = i + 1


def hidden_obligation_ok() -> None:
    Requires(MustTerminate(2))
    i = 0
    n = 10
    while i < n:
        Invariant(Implies(i > n, MustTerminate(n+i)))
        Invariant(Implies(False, MustTerminate(1)))
        Invariant(Implies(i <= n, MustTerminate(n-i+1)))
        i = i + 1
