from contracts.contracts import *


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value) and self.value == 0)  # type: ignore
        self.value = 0


def updatingId(b: bool, c: Container) -> bool:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == Old(c.value) + 1)
    Ensures(Result() == b)
    c.value += 1
    return b


def testAnd(b1: bool, b2: bool) -> bool:
    Ensures(Implies(Result(), b1))
    Ensures(Implies(Result(), b2))
    c = Container()
    res = updatingId(b1, c) and updatingId(b2, c)
    Assert(Implies(b1, c.value == 2))
    Assert(Implies(not b1, c.value == 1))
    return res


def testOr(b1: bool, b2: bool) -> bool:
    Ensures(Implies(b1, Result()))
    Ensures(Implies(b2, Result()))
    c = Container()
    res = updatingId(b1, c) or updatingId(b2, c)
    Assert(Implies(not b1, c.value == 2))
    Assert(Implies(b1, c.value == 1))
    return res


def testAndFail(b1: bool, b2: bool) -> bool:
    Ensures(Implies(Result(), b1))
    Ensures(Implies(Result(), b2))
    c = Container()
    Assert(c.value == 0)
    res = updatingId(b1, c) and updatingId(b2, c)
    Assert(c.value != 0)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c.value == 2 or c.value == 0)
    return res


def testOrFail(b1: bool, b2: bool) -> bool:
    Ensures(Implies(b1, Result()))
    Ensures(Implies(b2, Result()))
    c = Container()
    Assert(c.value == 0)
    res = updatingId(b1, c) or updatingId(b2, c)
    Assert(c.value != 0)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c.value == 2 or c.value == 0)
    return res


def updatingIdInt(b: int, c: Container) -> int:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == Old(c.value) + 1)
    Ensures(Result() == b)
    c.value += 1
    return b


def testTernary(b: bool) -> int:
    Ensures(Implies(b, Result() == 15))
    Ensures(Implies(not b, Result() == 32))
    c1 = Container()
    c2 = Container()
    res = updatingIdInt(15, c1) if updatingId(b, c1) else updatingIdInt(32, c2)
    Assert(c1.value >= 1)
    Assert(Implies(b, c1.value == 2))
    Assert(Implies(b, c2.value == 0))
    Assert(Implies(not b, c1.value == 1))
    Assert(Implies(not b, c2.value == 1))
    return res


def testTernaryFail(b: bool) -> int:
    Ensures(Implies(b, Result() == 15))
    Ensures(Implies(not b, Result() == 32))
    c1 = Container()
    c2 = Container()
    res = updatingIdInt(15, c1) if updatingId(b, c1) else updatingIdInt(32, c2)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(c1.value + c2.value != 2)
    return res
