from nagini_contracts.contracts import *
from typing import List

def test_list_3(r: List[int]) -> None:
    #:: ExpectedOutput(not.wellformed:insufficient.permission)|ExpectedOutput(carbon)(not.wellformed:insufficient.permission)
    Requires(Forall(r, lambda i: (i > 0, [])))

    a = 3
