# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    def some_method(self) -> int:
        Ensures(Result() >= 14)
        return 14


class Sub(Super):
    def some_method(self) -> int:
        Ensures(Result() >= 15)
        #:: ExpectedOutput(invalid.program:invalid.super.call)
        return 1 + super(True, self).some_method()