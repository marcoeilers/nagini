from nagini_contracts.contracts import *
from typing import Optional


class Cont1:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 2

    def m(self) -> None:
        return


class Cont2:
    pass


def return_optional(b: bool) -> Optional[Cont1]:
    if b:
        return None
    else:
        return Cont1()


OptionalCont1 = Optional[Cont1]


def return_optional_fail(b: bool) -> None:
    result = object()
    if b:
        result = None
    else:
        result = Cont2()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(result, OptionalCont1)


def param(o1: Optional[Cont1]) -> None:
    if o1 is not None:
        assert isinstance(o1, Cont1)
    assert not isinstance(o1, Cont2)


def param_2(o1: Optional[Cont1]) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert o1 is None


def param_3(o1: Optional[Cont1]) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert o1 is not None


def param_4(o1: Optional[Cont1]) -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert isinstance(o1, Cont1)


def param_5(o1: Optional[Cont1]) -> None:
    assert isinstance(o1, object)


def field_access(o1: Optional[Cont1], b: bool) -> None:
    Requires(Implies(b, o1 is not None and Acc(o1.v)))
    if b:
        a = o1.v
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c = o1.v


def field_reading(o1: Optional[Cont1]) -> None:
    Requires(Acc(o1.v))
    x = o1.v


def field_writing(o1: Optional[Cont1]) -> None:
    Requires(Acc(o1.v))
    o1.v = 4


def method_access(o1: Optional[Cont1], b: bool) -> None:
    Requires(Implies(b, o1 is not None))
    if b:
        o1.m()
    #:: ExpectedOutput(call.precondition:assertion.false)
    o1.m()