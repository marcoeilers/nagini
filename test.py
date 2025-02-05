from nagini_contracts.contracts import *
from typing import  List
class mycoolclass:
    def __init__(self, arg:int )->None:
        self.arg = arg

@ContractOnly
@Native
def test(i: int, i2: int, c: mycoolclass) -> int:
    Requires(i > 0)
    Requires(i2 > 0 and c.arg > 0)
    Ensures(Result() > 0)
    a = i
    return a + i2