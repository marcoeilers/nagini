from py2viper_contracts.contracts import (
    Assert,
)
from typing import Optional


class B:
    pass


class C:
    pass


def callee_3(b: Optional[B], c: Optional[C]) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(b is not c)


def test_3() -> None:
    callee_3(None, None)


def test2() -> None:
    Assert(None is None)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(None is not None)


def callee(b: B, c: C) -> None:
    Assert(b is not c)


def test() -> None:
    #:: ExpectedOutput(application.precondition:assertion.false)|OptionalOutput(application.precondition:assertion.false)
    callee(None, None)
