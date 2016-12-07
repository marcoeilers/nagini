#:: IgnoreFile(48)
from py2viper_contracts.contracts import *


class Super:
    pass


@Predicate
def P(s: Super) -> bool:
    return True

def exhale(s: Super) -> None:
    Requires(Acc(P(s), 0/1))

def test(a: Super) -> None:
    mydict = {} # type: Dict[int, int]
    mydict[1] = 1
    exhale(a)
    mydict[7] = 2
    exhale(a)
    Assert(mydict[1] == 1)
