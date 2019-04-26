# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 12

    @property
    def vtt(self) -> int:
        Requires(Acc(self.v))
        return self.v * 2

    @vtt.setter
    def vtt(self, vhalvs: int) -> None:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        Ensures(self.v == vhalvs // 2)
        self.v = vhalvs // 2

    #:: ExpectedOutput(function.not.wellformed:insufficient.permission)
    @property
    def vtt_2(self) -> int:
        return self.v

    @vtt_2.setter
    def vtt_2(self, vhalvs: int) -> None:
        #:: ExpectedOutput(assignment.failed:insufficient.permission)
        self.v = vhalvs // 2

    @property
    def vtt_3(self) -> int:
        Requires(Acc(self.v))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() == self.v)
        return self.v * 2

    @vtt_3.setter
    def vtt_3(self, vhalvs: int) -> None:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(self.v == vhalvs // 3)
        self.v = vhalvs // 2

    @property
    def vtt_4(self) -> int:
        Requires(Acc(self.v))
        return self.v * 2

    @property
    def slf(self) -> 'A':
        return self


def read() -> None:
    a = A()
    a1 = a.vtt
    a4 = a.vtt_4
    assert a1 == a4
    assert a1 == a.v * 2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def read_no_perm(a: A) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)
    o = a.vtt  # type: object


def write(a: A) -> None:
    Requires(Acc(a.v))
    Ensures(Acc(a.v))
    Ensures(a.vtt == 12)
    a.vtt = 12
    assert a.v == 6
    assert a.vtt == 12
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False


def write_no_perm(a: A) -> None:
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    a.vtt = 14


def chained(a: A) -> None:
    Requires(Acc(a.v))
    a.slf.slf.vtt = 8
    assert a.slf.slf.slf.slf.vtt == 8
    assert a.v == 4
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert False