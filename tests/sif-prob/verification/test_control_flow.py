# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List
from nagini_contracts.contracts import *


def test_if_fail(i: int) -> int:
    res = 12
    #:: ExpectedOutput(probabilistic.sif.violated:high.branch)
    if i:
        res = 15
    return res


def test_if(i: int) -> int:
    Requires(Low(i))
    res = 12
    if i:
        res = 15
    return res

# while

def test_while_fail(n: int) -> int:
    i = 0
    #:: ExpectedOutput(probabilistic.sif.violated:high.branch)
    while i < n:
        i -= 1
    return 12


def test_while(n: int) -> int:
    Requires(Low(n))
    i = 0
    while i < n:
        Invariant(Low(i))
        i -= 1
    return 12

# for

def test_for_fail(n: int) -> int:
    Requires(n > 0)
    res = 0
    #:: ExpectedOutput(probabilistic.sif.violated:high.branch)
    for i in range(0, n):
        res += 1
    return res


def test_for(n: int) -> int:
    Requires(n > 0)
    Requires(Low(n))
    res = 0
    for i in range(0, n):
        Invariant(Low(Previous(i)))
        res += 1
    return res

# call receiver

class Super:

    def foo(self) -> int:
        Ensures(Low(Result()))
        return 6


class Sub(Super):

    def foo(self) -> int:
        Ensures(Low(Result()))
        return 6


def test_receiver_fail(s: Super) -> int:
    #:: ExpectedOutput(probabilistic.sif.violated:high.receiver.type)
    s.foo()
    return 5


def test_receiver(s: Super) -> int:
    Requires(Low(type(s)))
    s.foo()
    return 5

# exception


def test_exception_fail(e: Exception) -> None:
    Ensures(True)
    Exsures(Exception, True)
    #:: ExpectedOutput(probabilistic.sif.violated:high.exception.type)
    raise e


def test_exception(e: Exception) -> None:
    Requires(Low(type(e)))
    Ensures(True)
    Exsures(Exception, True)
    raise e

# lowevent trivial

@ContractOnly
def myprint(i: int) -> None:
    Requires(Low(i))
    Requires(LowEvent())


def caller(i: int) -> None:
    Requires(Low(i))
    myprint(i)

# and

def effects() -> int:
    Ensures(Low(Result()))
    Ensures(Result() is 5)
    return 5

def test_and_fail(o: int) -> int:
    #:: ExpectedOutput(probabilistic.sif.violated:high.short.circuit)
    res = o and effects()
    return res

def test_and_allow_in_spec(o: int) -> int:
    Ensures(Result() == (o and 5))
    bo = bool(o)
    res = ((1-bo) * o) + (bo * 5)
    return res

def test_and(o: int) -> int:
    Requires(LowVal(bool(o)))
    res = o and effects()
    return res

# or

def test_or_fail(o: int) -> int:
    #:: ExpectedOutput(probabilistic.sif.violated:high.short.circuit)
    res = o or effects()
    return res


def test_or(o: int) -> int:
    Requires(LowVal(bool(o)))
    res = o or effects()
    return res

# condexp

def test_condexp_fail(i: int) -> int:
    #:: ExpectedOutput(probabilistic.sif.violated:high.branch)
    res = 12 if i else effects()
    return res


def test_condexp(i: int) -> int:
    Requires(Low(i))
    res = 12 if i else effects()
    return res


def test_condexp_allowed_in_spec(i: bool, i2: int, i3: int) -> int:
    Ensures(Result() == (i2 if i else i3))
    res = ((i * i2) + ((1-i)) * i3)
    return res


def test_condexp_allowed_in_contract_func(i: bool, i2: int, i3: int) -> int:
    res = ((i * i2) + ((1-i)) * i3)
    Assert(res == (i2 if i else i3))
    return res


# comprehensions

def test_comprehension_fail(l: List[int]) -> List[int]:
    Requires(Acc(list_pred(l)))
    #:: ExpectedOutput(probabilistic.sif.violated:high.comprehension)
    return [5+e for e in l]


def test_comprehension(l: List[int]) -> List[int]:
    Requires(Acc(list_pred(l)))
    Requires(Low(len(l)))
    return [5+e for e in l]
