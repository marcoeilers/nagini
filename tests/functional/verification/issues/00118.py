from nagini_contracts.contracts import *
from typing import List, Optional, Union

class Super:
    pass

def test_union_function(u: Union[List[int], int]) -> None:
    Requires(Implies(isinstance(u, list), list_pred(u)))
    if not u:
        if isinstance(u, int):
            assert u == 0
        else:
            assert len(u) == 0

def test_union_no_position() -> None:
    empty = []  # type: List[int]
    a = 3 or empty
    assert a == 3

def test_union_optional(a: int) -> int:
    Ensures(Implies(a == 44, Result() == 88))
    Ensures(Implies(a != 44, Result() == 99))
    c = Super()  # type: Optional[Super]
    if a == 44:
        c = None
    return 99 if c is not None else 88
