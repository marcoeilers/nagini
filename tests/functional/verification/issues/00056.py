from py2viper_contracts.contracts import (
    Acc,
    Assert,
    Requires,
)


class B:
    pass


class C:
    pass


class A:

    def __init__(self) -> None:
        self.b = None   # type: B
        self.c = None   # type: C

    def test(self) -> None:
        Requires(Acc(self.b) and Acc(self.c))
        #:: UnexpectedOutput(assert.failed:assertion.false, /py2viper/issue/56/)
        Assert(self.b is not self.c)
