from nagini_contracts.contracts import *
from typing import List
class A:
    def __init__(self, y: int):
        self.y = y
        
@ContractOnly
@Native
def first_last_swap(n: A, l:List[int]) -> int:
    Requires(Acc(n.y, 1/2) and list_pred(l) 
            and len(l) > 0)
    Ensures(Acc(n.y, 1/2) and list_pred(l)     
            and len(l) == Old(len(l))
            and Forall(int, lambda i: Implies(i >= 0 and i < len(l)-1, l[i] is Old(l[i])))
            and l[len(l)-1] is Old(n.y) and n.y is Old(l[len(l)-1]) 
            and Result() == len(l) )