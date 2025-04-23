from nagini_contracts.contracts import *
from typing import List
@ContractOnly
@Native
def first_last_swap(l:List[int]) -> int:
    Requires(list_pred(l) and len(l) > 0)
    Ensures(list_pred(l) and len(l) == Old(len(l)) and
            Forall(int, lambda i: Implies(i > 0 and i < len(l)-1, l[i] is Old(l[i])))
            and l[len(l)-1] is Old(l[0]) 
            and l[0] is Old(l[len(l)-1])
            and Result() == (1 if len(l) == 1 else 0))