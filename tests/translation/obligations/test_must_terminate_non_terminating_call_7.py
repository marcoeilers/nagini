from py2viper_contracts.contracts import (
    Requires,
    Invariant,
)
from py2viper_contracts.obligations import *


def non_terminating() -> None:
    pass


def test_call_non_terminating_5() -> None:
    Requires(MustTerminate(2))
    a = [1, 2, 3]
    i = 0
    for elem in a:
        Invariant(MustTerminate(len(a) - i))
        i += 1
    #:: ExpectedOutput(invalid.program:non_terminating_call_in_terminating_context)
    non_terminating()
