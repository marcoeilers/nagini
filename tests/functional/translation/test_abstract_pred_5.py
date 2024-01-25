from nagini_contracts.contracts import *


class MyClass:
    def __init__(self) -> None:
        self.x = 1

    @Predicate
    @ContractOnly
    def myHuh(self) -> bool:
        return self.x > 2


class MySubClass(MyClass):

    @Predicate  #:: ExpectedOutput(invalid.program:partially.abstract.predicate.family)
    def myHuh(self) -> bool:
        return self.x > 4

