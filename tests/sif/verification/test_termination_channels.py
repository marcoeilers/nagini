# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# --- While loops ---

def loop_no_lowevent(h: int) -> None:
    Requires(Low(h))
    x = h
    while x != 0:
        Invariant(x <= h)
        Invariant(Implies(h >= 0, x >= 0))
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.not_lowevent)
        Invariant(TerminatesSif(h >= 0, x))
        x -= 1

def loop_termcond_high(h: int) -> None:
    Requires(LowEvent())
    x = h
    while x != 0:
        Invariant(x <= h)
        Invariant(Implies(h >= 0, x >= 0))
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(h >= 0, x))
        x -= 1

def loop_termcond_not_tight(h: int) -> None:
    Requires(LowEvent())
    Requires(Low(h))
    x = h
    while x != 0:
        Invariant(x <= h)
        Invariant(Implies(h > 0, x >= 0))
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_tight)
        Invariant(TerminatesSif(h > 0, x))
        x -= 1

def loop_fixed(l: int) -> None:
    Requires(LowEvent())
    Requires(Low(l))
    x = l
    while x != 0:
        Invariant(x <= l)
        Invariant(Implies(l >= 0, x >= 0))
        Invariant(TerminatesSif(l >= 0, x))
        x -= 1

def continue_infinite() -> None:
    x = 10
    #:: ExpectedOutput(leak_check.failed:must_terminate.loop_promise_not_kept)
    while x > 0:
        Invariant(x >= 0 and x <= 10)
        Invariant(TerminatesSif(True, x))
        if True:
            continue
        x -= 1

def return_ok() -> None:
    Requires(LowEvent())
    x = 10
    while True:
        Invariant(x >= 0 and x <= 10)
        Invariant(TerminatesSif(True, x + 1))
        if x == 0:
            return
        x -= 1

def nested(h: int) -> None:
    x1 = h
    #:: ExpectedOutput(carbon)(leak_check.failed:must_terminate.loop_promise_not_kept)
    while x1 != 0:
        Invariant(x1 <= h)
        Invariant(Implies(h >= 0, x1 >= 0))
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)|ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.not_lowevent)
        Invariant(TerminatesSif(h >= 0, x1))
        x2 = 10
        while x2 != 0:
            Invariant(x2 >= 0 and x2 <= 10)
            Invariant(TerminatesSif(True, x2))
            x2 -= 1

# --- Recursion ---

def terminates(x: int) -> int:
    Requires(TerminatesSif(True, 1))
    Ensures(Result() is x)
    return x

def recursion(h: int) -> int:
    #:: ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.condition_not_tight)
    Requires(TerminatesSif(h > 0, h + 2))
    Ensures(Result() == 1)
    x = terminates(h)
    if x == 0:
        return 1
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)|ExpectedOutput(carbon)(call.precondition:sif_termination.not_lowevent)
    return recursion(x - 1)

def recursion_fixed(h: int) -> int:
    Requires(TerminatesSif(h >= 0, h + 2))
    Ensures(Result() == 1)
    x = terminates(h)
    if x == 0:
        return 1
    return recursion_fixed(x - 1)

def test_recursion(secret: int) -> int:
    #:: ExpectedOutput(call.precondition:sif_termination.condition_not_low)|ExpectedOutput(carbon)(call.precondition:sif_termination.not_lowevent)
    return recursion_fixed(secret)

def cycle_1(h: int) -> None:
    Requires(TerminatesSif(True, h))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    cycle_2(h)

def cycle_2(h: int) -> None:
    Requires(TerminatesSif(True, h))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    cycle_1(h)
