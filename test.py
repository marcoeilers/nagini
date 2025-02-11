from nagini_contracts.contracts import *
from typing import List


class mycoolclass:
    def __init__(self, arg: int) -> None:
        self.arg = arg
@Predicate
def pred(x: mycoolclass, i: int) -> bool:
    return True

def test(i: int, i2: int, c: mycoolclass) -> int:
    Requires(i > 13 and i > i2+3 and pred(c, i))
    Requires(i2 > 0 and ((Acc(c.arg) and c.arg > 0) if i2 > 0 else True))
    Ensures(Result() > 13)
    a = i
    return a + i2
