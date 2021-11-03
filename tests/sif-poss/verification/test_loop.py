# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def while_cond_low_fail(n: int) -> None:
    Requires(LowEvent())
    i = 0
    #:: ExpectedOutput(possibilistic.sif.violated:high.branch)
    while i < n:
        i += 1


def while_cond_low(n: int) -> None:
    Requires(Low(n))
    Requires(LowEvent())
    i = 0
    while i < n:
        Invariant(Low(i))
        i += 1


def while_cond_low_fail_not_lowevent(n: int) -> None:
    Requires(Low(n))
    i = 0
    #:: ExpectedOutput(possibilistic.sif.violated:high.branch)
    while i < n:
        Invariant(Low(i))
        i += 1


def while_terminatessif(n: int) -> None:
    Requires(Low(n))
    Requires(LowEvent())
    i = 0
    while i != n:
        Invariant(i >= 0)
        Invariant(TerminatesSif(n >= 0, n-i))
        i += 1


def while_terminatessif_fail(n: int) -> None:
    Requires(LowEvent())
    i = 0
    while i != n:
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)|ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.condition_not_tight)
        Invariant(TerminatesSif(n >= 0, n-i))
        i += 1


def for_cond_low_fail(n: int) -> int:
    Requires(n > 0)
    Requires(LowEvent())
    res = 0
    #:: ExpectedOutput(possibilistic.sif.violated:high.branch)
    for i in range(0, n):
        res += 1
    return res


def for_cond_low(n: int) -> int:
    Requires(n > 0)
    Requires(Low(n))
    Requires(LowEvent())
    res = 0
    for i in range(0, n):
        Invariant(Low(Previous(i)))
        res += 1
    return res


def for_cond_low_fail_not_lowevent(n: int) -> int:
    Requires(n > 0)
    Requires(Low(n))
    res = 0
    #:: ExpectedOutput(possibilistic.sif.violated:high.branch)
    for i in range(0, n):
        Invariant(Low(Previous(i)))
        res += 1
    return res


def for_terminatessif(n: int) -> int:
    Requires(n > 0)
    Requires(Low(n))
    Requires(LowEvent())
    res = 0
    for i in range(0, n):
        Invariant(Low(Previous(i)))
        Invariant(TerminatesSif(True, n - len(Previous(i))))
        res += 1
    return res


def for_terminatessif_fail(n: int) -> int:
    Requires(n > 0)
    Requires(LowEvent())
    res = 0
    for i in range(0, n):
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)|ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.condition_not_tight)
        Invariant(TerminatesSif(n > 1, n - len(Previous(i))))
        res += 1
    return res