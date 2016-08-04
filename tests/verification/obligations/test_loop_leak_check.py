from py2viper_contracts.contracts import (
    Requires,
    Invariant,
    Implies,
)
from py2viper_contracts.io import *
from py2viper_contracts.obligations import MustTerminate


def context_1(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    #:: ExpectedOutput(leak_check.failed:loop_context.has_unsatisfied_obligations)
    while i < 5:
        i += 1


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def context_2(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    while i < 5:
        Invariant(MustTerminate(5 - i))
        i += 1


#:: OptionalOutput(leak_check.failed:method_body.leaks_obligations)
def body_1(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    # Error
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(token(t1, 1))
        i += 1


def body_2(t1: Place) -> None:
    Requires(token(t1, 1))
    i = 0
    # Error
    #:: OptionalOutput(leak_check.failed:loop_body.leaks_obligations)
    while i < 5:
        #:: ExpectedOutput(invariant.not.preserved:insufficient.permission)
        Invariant(Implies(i < 5, token(t1, 1)))
        i += 1
