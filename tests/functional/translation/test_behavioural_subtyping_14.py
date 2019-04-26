# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        self.value = "Avalue"

    @classmethod
    def construct(cls) -> object:
        Ensures(isinstance(Result(), cls))
        return cls()


class B(A):
    #:: ExpectedOutput(invalid.program:invalid.override)
    def __init__(self, b: B) -> None:
        self.value = "Bvalue"
