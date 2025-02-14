from nagini_contracts.contracts import *
from typing import List


class mycoolclass:
    def __init__(self, arg: int) -> None:
        self.arg = arg


@Predicate
def pred(x: mycoolclass, i: int) -> bool:
    return True

@Pure
def purefunction(x: mycoolclass, i: int) -> int:
    return 123

def method(x: mycoolclass, i: int) -> int:
    Requires(Acc(x.arg))
    x.arg = 123
    return 1


@ContractOnly
@Native
def compare(i: int, i2: int, c: mycoolclass) -> int:
    #Requires((i + 2) >= 13)
    #Requires((i+i2 > 0) if ((i + 2) == 13) else True)
    Requires(i is i2)
    Requires(pred(c, i))
    #Requires(Acc(c.arg))
    Ensures(Result() > 13)


def test2(i: int, i2: int, c: mycoolclass) -> int:
    Requires(i > 13)
    Requires(i2 > 0)
    Requires(Acc(pred(c,i)))
    Ensures(Result() > 13)
    a = i
    return a + i2


def test(i: int, i2: int, c: mycoolclass) -> int:
    Requires(i > 13 and i > i2+3 and pred(c, i))
    Requires((pred(c, i) if i > 4 else i2 == 0))
    Requires(i2 > 0 and ((Acc(c.arg) and c.arg > 0) if i2 > 0 else True))
    Ensures(Result() > 13)
    a = i
    return a + i2
