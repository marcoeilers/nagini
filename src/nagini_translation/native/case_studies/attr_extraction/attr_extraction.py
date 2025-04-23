from nagini_contracts.contracts import *
from typing import List
class A:
    def __init__(self, y: int):
        self.y = y
        
@ContractOnly
@Native
def replace_and_get(n: A, i:int) -> int:
    Requires(Acc(n.y))
    Ensures(Acc(n.y) and n.y is i and Result() is Old(n.y))