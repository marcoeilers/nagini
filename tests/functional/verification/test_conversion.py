# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional

class Super:
    pass

class Sub(Super):
    pass


@Pure
def test_ifexp(a: int) -> int:
    Ensures(Implies(a == 0, Result() == 66))
    Ensures(Implies(a != 0, Result() == 55))
    return 55 if a else 66


@Pure
def test_ifexp_wrong(a: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(a == 0, Result() == 55))
    return 55 if a else 66


def test_not(a: int) -> bool:
    Ensures(Implies(Result(), a == -17))
    return not (a + 17)


def test_not_wrong(a: int) -> bool:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(not Result(), a == -17))
    return not (a + 17)


def test_if(a: int) -> int:
    Ensures(Implies(a == 0, Result() == 66))
    Ensures(Implies(a != 0, Result() == 55))
    if a:
        return 55
    else:
        return 66


def test_if_wrong(a: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(a == 0, Result() == 55))
    if a:
        return 55
    else:
        return 66


def test_while(a: int) -> int:
    Requires(a >= 0)
    Ensures(Result() == a)
    b = a
    c = 0
    while b:
        Invariant(b + c == a)
        c += 1
        b -= 1
    return c


def test_while_wrong(a: int) -> int:
    Requires(a >= 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == a + 2)
    b = a
    c = 0
    while b:
        Invariant(b + c == a)
        c += 1
        b -= 1
    return c


def test_none_super(a: int) -> int:
    Ensures(Implies(a == 44, Result() == 88))
    Ensures(Implies(a != 44, Result() == 99))
    c = Super()  # type: Optional[Super]
    if a == 44:
        c = None
    return 99 if c else 88


def test_none_super_wrong(a: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(a == 44, Result() == 77))
    c = Super()  # type: Optional[Super]
    if a == 44:
        c = None
    return 99 if c else 88


def test_param_object(a: int, b: Optional[object]) -> int:
    Ensures(Implies(b == None, Result() == 88))
    return 99 if b else 88


def test_param_object_wrong(a: int, b: Optional[object]) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(b is not None, Result() == 77))
    return 99 if b else 88


def test_param_sub(a: int, b: Optional[Sub]) -> int:
    Ensures(Implies(b == None, Result() == 88))
    Ensures(Implies(b != None, Result() == 99))
    return 99 if b else 88


def test_param_sub_wrong(a: int, b: Optional[Sub]) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Implies(b is not None, Result() == 98))
    return 99 if b else 88


def test_list(a: int) -> None:
    super1 = Super()
    sub1 = Sub()
    b = [] # type: List[int]
    c = [super1, super1, sub1]
    Assert(True if c else False)
    Assert(False if b else True)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(True if b else False)


def test_set(a: int) -> bool:
    b = set() # type: Set[int]
    c = {1,2,3}
    Assert(True if c else False)
    Assert(False if b else True)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(True if b else False)


def test_dict(a: int) -> bool:
    super1 = Super()
    sub1 = Sub()
    b = {} # type: Dict[int, object]
    c = {1 : super1, 2: sub1}
    Assert(True if c else False)
    Assert(False if b else True)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(True if b else False)