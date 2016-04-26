from py2viper_contracts.contracts import *

class A:

    def first(self) -> int:
        return A.second(self)

    def second(self) -> int:
        return A.first(self)