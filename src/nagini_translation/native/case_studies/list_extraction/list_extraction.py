from nagini_contracts.contracts import *
from typing import List
@ContractOnly
@Native
def first_swap(l:List[int], i:int) -> int:
    Requires(list_pred(l) and len(l) > 0)
    Ensures(list_pred(l) and len(l) == Old(len(l)) and
            Forall(int, lambda j: Implies(j >= 0 and j < len(l), l[j] is Old(l[j])))
            and Result() is Old(l[i]))