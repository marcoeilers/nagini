# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value) and self.value == 0)  # type: ignore
        self.value = 0


def break_out(c: Container) -> None:
    Requires(Acc(c.value))
    Ensures(Acc(c.value) and c.value == 5)
    while True:
        Invariant(Acc(c.value))
        try:
            raise Exception()
        finally:
            break
    c.value = 5


def break_out_2(c: Container) -> None:
    Requires(Acc(c.value))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.value) and c.value == 6)
    while True:
        Invariant(Acc(c.value))
        try:
            raise Exception()
        finally:
            break
    c.value = 5