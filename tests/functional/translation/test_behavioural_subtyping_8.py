# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class MyException(Exception):
    pass


class MySpecialException(MyException):
    pass


class MyOtherException(Exception):
    pass


class Super:
    def some_function(self, a: int) -> int:
        Requires(a >= 0)
        Ensures(Result() > 17)
        Exsures(MyException, True)
        return 18 + a


class Sub(Super):
    #:: ExpectedOutput(invalid.program:invalid.override)
    def some_function(self, a: int) -> int:
        Requires(True)
        Ensures(Result() > 17)
        Exsures(MySpecialException, True)
        Exsures(MyOtherException, True)
        return 19
