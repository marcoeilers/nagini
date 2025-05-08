from nagini_contracts.contracts import *
from typing import List
@ContractOnly
@Native
def list_extraction(l:List[int], i:int) -> int:
    Requires(list_pred(l))
    Requires(len(l) > i and i >= 0 and len(l) < 100)
    Ensures(list_pred(l) and len(l) == Old(len(l)))
    Ensures(Forall(int, lambda j: Implies(j >= 0 and j < len(l), l[j] is Old(l[j]))))
    Ensures(Result() is Old(l[i]))
            