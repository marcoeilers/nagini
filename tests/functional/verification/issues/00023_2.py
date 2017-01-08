from py2viper_contracts.contracts import *
from typing import Tuple


def bla() -> Tuple[int, str]:
    #:: ExpectedOutput(application.precondition:assertion.false)
    Ensures(Result()[0] == "bla" and Result()[1] == 2)
    return 2, "bla"
