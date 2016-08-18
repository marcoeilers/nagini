from py2viper_contracts.contracts import (
    Requires,
)
from py2viper_contracts.obligations import *
from threading import Lock


def test(lock: Lock) -> None:
    #:: ExpectedOutput(invalid.program:obligation.fresh.in_precondition)
    Requires(MustRelease(lock))
