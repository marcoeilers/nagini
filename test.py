from nagini_contracts.contracts import *
from typing import  List
class mycoolclass:
    def __init__(self, arg:int )->None:
        self.arg = arg

@ContractOnly
@Native
def test(i: int, i2: int, c: mycoolclass) -> int:
    a = i
    return a + i2