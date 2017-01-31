from py2viper_contracts.contracts import *


class Super:
    def some_method(self) -> int:
        Ensures(Result() >= 14)
        return 14
    
    
class Sub(Super):
    def some_method(self) -> int:
        Ensures(Result() >= 15)
        return 1 + super().some_method()

    def some_method_3(self) -> int:
        Ensures(Result() >= 15)
        return 1 + super(Sub, self).some_method()

    def some_method_4(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() >= 16)
        return 1 + super(Sub, self).some_method()

    def some_method_2(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Result() >= 16)
        return 1 + super().some_method()