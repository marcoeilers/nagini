from py2viper_contracts.contracts import *


class SuperA:
    def __init__(self) -> None:
        self.int_field = 14
        self.bool_field = True

    def some_method(self, a: int) -> int:
        return a


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
    #:: ExpectedOutput(type.error:Argument 1 of "some_method" incompatible with supertype "SuperF")
    def some_method(self, a : SubSubA, b : SubSubA) -> SubA:
        return b