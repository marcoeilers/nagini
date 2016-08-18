from py2viper_contracts.contracts import (
    Assert,
)


class B:
    pass


class C:
    pass


def callee(b: B, c: C) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)|MissingOutput(assert.failed:assertion.false, /py2viper/issue/57/)
    Assert(b is not c)


def test() -> None:
    callee(None, None)


def test2() -> None:
    Assert(None is None)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(None is not None)
