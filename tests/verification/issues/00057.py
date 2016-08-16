from py2viper_contracts.contracts import (
    Assert,
)


class B:
    pass


class C:
    pass


def callee(b: B, c: C) -> None:
    Assert(b is not c)


def test() -> None:
    callee(None, None)
