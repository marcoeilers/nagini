from threading import Lock

from py2viper_contracts.contracts import (
    Assert,
    Invariant,
    Requires,
    Ensures,
)
from py2viper_contracts.obligations import *


#:: OptionalOutput(leak_check.failed:method_body.leaks_obligations)
def acquire_1(l: Lock) -> None:
    #:: ExpectedOutput(call.precondition:assertion.false)
    l.acquire()


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def acquire_2(l: Lock) -> None:
    Requires(l is not None)
    l.acquire()


def acquire_3(l: Lock) -> None:
    Requires(l is not None)
    l.acquire()
    l.release()


def acquire_4(l: Lock) -> None:
    Requires(l is not None)
    Ensures(MustRelease(l))
    l.acquire()


def acquire_5(l: Lock) -> None:
    Requires(l is not None)
    Ensures(MustRelease(l, 10))
    l.acquire()
