# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SuperA:
    def __init__(self) -> None:
        self.int_field = 14
        self.bool_field = True

    def some_method(self, b: int) -> int:
        return b


class SubA(SuperA):
    def some_method(self, b: int) -> int:
        return b + 5


class SubSubA(SubA):
    def some_method(self, b: int) -> int:
        return b + 9


class SuperF:
    def some_method(self, b: SubA, a: SubSubA) -> SubA:
        return a


class SubF1(SuperF):
    #:: ExpectedOutput(type.error:Signature of "some_method" incompatible with supertype "SuperF")
    def some_method(self, b: SubA, a: SubSubA, c: SuperA) -> SubA:
        return a
