# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# Basic tests with normal conditions
class SuperA:
    def __init__(self) -> None:
        self.int_field = 14
        self.bool_field = True

    def some_method(self, b: int) -> int:
        Requires(b > 9)
        Ensures(Result() > 9)
        return b


class SubA(SuperA):
    def some_method(self, b: int) -> int:
        Requires(b > 5)
        Ensures(Result() > 10)
        return b + 5


class SubSubA(SubA):
    def some_method(self, b: int) -> int:
        Requires(b > 3)
        Ensures(Result() > 12)
        return b + 9


class SuperB:
    #:: Label(L1)
    def some_method(self, b: int) -> int:
        Requires(b > 9)
        Ensures(Result() > 9)
        return b


class SubB(SuperB):
    #:: ExpectedOutput(call.precondition:assertion.false,L1)|Label(L2)
    def some_method(self, b: int) -> int:
        Requires(b > 10)
        Ensures(Result() > 10)
        return b + 5


class SubSubB(SubB):
    #ExpectedOutput(call.precondition:assertion.false,L2)  # not expected because not selected
    def some_method(self, b: int) -> int:
        Requires(b > 11)
        Ensures(Result() > 10)
        return b + 5

