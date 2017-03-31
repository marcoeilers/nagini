from nagini_contracts.contracts import *
from typing import List, Optional


class B:
    pass


class A:
    #:: ExpectedOutput(invalid.program:local.type.alias)
    MY_TYPE4 = List[B]