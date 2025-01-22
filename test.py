from nagini_contracts.contracts import *
from typing import  List

@ContractOnly
@Native
def test(i: int, i2: int) -> int:
    a = i
    return a + i2