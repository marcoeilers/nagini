from nagini_contracts.contracts import *
from typing import List
@Pure
def fibo(n):
    return 1 if n <= 0 else fibo(n-1) + fibo(n-2)

@ContractOnly
@Native
def fibo_array(n: int) -> List[int]:
    Requires(n >= 0)
    Ensures(list_pred(Result()) and
            Forall(int, lambda i: Implies(i >= 0 and i < len(Result()), Result()[i] == fibo(i))))
           
    
