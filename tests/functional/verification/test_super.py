# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    def some_method(self) -> int:
        Ensures(Result() >= 14)

        # some code that is just here to make sure loops can be properly inlined
        input = 2
        out_a = input
        for i in range(2):
            Invariant(out_a == input * (input ** len(Previous(i))))
            out_a = out_a * input

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