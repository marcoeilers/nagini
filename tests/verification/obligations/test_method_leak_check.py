from py2viper_contracts.contracts import (
    Requires,
)
from py2viper_contracts.io import *
from py2viper_contracts.obligations import MustTerminate


def callee_1(t1: Place) -> None:
    pass


def caller_1(t1: Place) -> None:
    Requires(token(t1, 1))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    callee_1(t1)


def callee_2(t1: Place) -> None:
    Requires(MustTerminate(1))


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def caller_2(t1: Place) -> None:
    Requires(token(t1, 1))
    callee_2(t1)


#:: ExpectedOutput(leak_check.failed:method_body.leaks_obligations)
def body(t1: Place) -> None:
    Requires(token(t1, 1))
