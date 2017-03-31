from nagini_contracts.contracts import *
from typing import List, Optional


class B:
    pass


def m() -> None:
    #:: ExpectedOutput(invalid.program:local.type.alias)
    MY_TYPE = List[B]