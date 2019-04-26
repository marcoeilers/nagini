# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Zero:
    def __init__(self) -> None:
        Ensures(Acc(self.v1))  # type: ignore
        self.v1 = 12

    @property
    def vtt(self) -> int:
        Requires(Acc(self.v1))
        return self.v1 * 2


class A(Zero):
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 12

    #:: ExpectedOutput(invalid.program:invalid.override)
    @property
    def vtt(self) -> int:
        Requires(Acc(self.v))
        return self.v * 2