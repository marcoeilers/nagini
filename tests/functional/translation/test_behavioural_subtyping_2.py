# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SuperA:
    def __init__(self) -> None:
        self.int_field = 14
        self.bool_field = True

    def some_method(self, a: int) -> int:
        return a


class SubA(SuperA):
    def some_method(self, a: int) -> int:
        return a + 5

class SubSubA(SubA):
    def some_method(self, a: int) -> int:
        return a + 9

class SuperF:
    def some_method(self, b: SubA, a: SubSubA) -> SubA:
        return a

class SubF1(SuperF):
    #:: ExpectedOutput(type.error:Argument 1 of "some_method" is incompatible with supertype "SuperF"; supertype defines the argument type as "SubA")
    def some_method(self, b: SubSubA, a: SubSubA) -> SubA:
        return a
