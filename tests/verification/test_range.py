from py2viper_contracts.contracts import *


def rangetest() -> None:
    a = range(0, 5)
    Assert(a[2] == 2)
    Assert(3 in a)
    Assert(7 not in a)
    Assert(5 not in a)
    Assert(Forall(a, lambda x: (x < 5, [])))
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(a, lambda x: (x < 4, [])))
