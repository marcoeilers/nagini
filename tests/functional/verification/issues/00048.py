# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    pass


@Predicate
def P(s: Super) -> bool:
    return True

def exhale(s: Super) -> None:
    Requires(Acc(P(s), 0/1))

def test(a: Super) -> None:
    Requires(Acc(P(a), 1/100))
    mydict = {} # type: Dict[int, int]
    mydict[1] = 1
    exhale(a)
    mydict[7] = 2
    exhale(a)
    mydict[3] = 2
    exhale(a)
    mydict[5] = 2
    exhale(a)
    mydict[2] = 2
    exhale(a)
    Assert(mydict[1] == 1)