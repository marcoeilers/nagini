from contracts.contracts import *

class SuperClass:
    def __init__(self) -> None:
        Ensures(Acc(self.superField) and self.superField == 12)
        Ensures(Acc(self.otherSuperField) and self.otherSuperField == 13)
        Ensures(Acc(self.__privateField) and self.__privateField == 15)
        self.superField = 12
        self.otherSuperField = 13
        self.__privateField = 15

    @Pure
    def getprivate(self) -> int:
        return self.__privateField


class SubClass(SuperClass):
    # need implicit constructor
    # needs to call super constructor
    # all constructors need to return acc, or at least standard ones do

    def setprivate(self, i: int) -> None:
        self.__privateField = i

    @Pure
    def getprivate(self) -> int:
        return self.__privateField