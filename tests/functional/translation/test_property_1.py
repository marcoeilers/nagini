# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.io_builtins import *


class A:
    def __init__(self) -> None:
        Ensures(Acc(self.v))  # type: ignore
        self.v = 12

    @property
    def vtt(self) -> int:
        Requires(Acc(self.v))
        return self.v * 2


def invalid_write(a: A) -> None:
    Requires(Acc(a.v))
    #:: ExpectedOutput(type.error:Property "vtt" defined in "A" is read-only)
    a.vtt = 12