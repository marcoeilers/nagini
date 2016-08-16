from py2viper_contracts.contracts import (
    Requires,
)
from py2viper_contracts.obligations import *


def non_terminating3() -> None:
    pass


def terminating_caller() -> None:
    Requires(MustTerminate(2))
    #:: ExpectedOutput(invalid.program:non_terminating_call_in_terminating_context)
    non_terminating3()
