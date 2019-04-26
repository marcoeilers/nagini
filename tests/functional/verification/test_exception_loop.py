# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value) and self.value == 0)  # type: ignore
        self.value = 0


def break_out_exception(c: Container, b: bool) -> None:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == 8)
    Exsures(Exception, Acc(c.value) and c.value == 7)
    while True:
        Invariant(Acc(c.value))
        if b:
            c.value = 7
            raise Exception()
        else:
            c.value = 8
            break


def break_out_exception_2(c: Container, b: bool) -> None:
    Requires(Acc(c.value))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.value) and c.value == 9)
    Exsures(Exception, Acc(c.value) and c.value == 7)
    while True:
        Invariant(Acc(c.value))
        if b:
            c.value = 7
            raise Exception()
        else:
            c.value = 8
            break


def break_out_exception_3(c: Container, b: bool) -> None:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == 8)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(Exception, Acc(c.value) and c.value == 9)
    while True:
        Invariant(Acc(c.value))
        if b:
            c.value = 7
            raise Exception()
        else:
            c.value = 8
            break


def break_out(c: Container, b: bool) -> Optional[int]:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == 8)
    while True:
        Invariant(Acc(c.value))
        c.value = 8
        break


def break_out_2(c: Container, b: bool) -> Optional[int]:
    Requires(Acc(c.value))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.value) and c.value == 9)
    while True:
        Invariant(Acc(c.value))
        c.value = 8
        break