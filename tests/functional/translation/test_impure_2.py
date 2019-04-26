# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 2


def m(a: A) -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Acc(a.v)