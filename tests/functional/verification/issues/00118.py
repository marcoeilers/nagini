from nagini_contracts.contracts import *
from typing import Union, List

def test_union_function(u: Union[List[int], int]) -> None:
    Requires(Implies(isinstance(u, list), list_pred(u)))
    if not u:
        if isinstance(u, int):
            assert u == 0
        else:
            assert len(u) == 0
