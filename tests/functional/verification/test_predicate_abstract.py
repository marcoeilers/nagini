from nagini_contracts.contracts import *


class MyClass:
    def __init__(self) -> None:
        self.x = 1

    @Predicate
    @ContractOnly
    def myHuh(self) -> bool:
        return self.x > 2


class MySubClass(MyClass):

    @Predicate
    @ContractOnly
    def myHuh(self) -> bool:
        return self.x > 4


@Predicate
@ContractOnly
def huh(mc: MyClass) -> bool:
    return mc.x > 6


@Pure
@ContractOnly
def huhFunc(mc: MyClass) -> int:
    Requires(huh(mc))
    Ensures(Result() > 0)
    return Unfolding(huh(mc), 6)
