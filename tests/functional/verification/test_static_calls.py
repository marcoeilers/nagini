# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class MyException(Exception):
    pass


class MySpecialException(MyException):
    pass


class MyOtherException(Exception):
    pass


class ParameterizedException(Exception):
    def __init__(self, num: int) -> None:
        Ensures(Acc(self.num))  # type: ignore
        Ensures(self.num == num)  # type: ignore
        self.num = num


class Container:
    def __init__(self) -> None:
        Ensures(Acc(self.value))  # type: ignore
        self.value = 0


class Super:
    def return_func(self, c: Container) -> int:
        Requires(Acc(c.value))
        Ensures(Acc(c.value) and Result() == c.value)
        return c.value

    def some_func(self, c: Container) -> int:
        Requires(Acc(c.value))
        Ensures(False)
        Exsures(MyOtherException, Acc(c.value) and c.value == Old(c.value) + 15)
        try:
            Super.other_func(self, c, True)
        except MySpecialException:
            Assert(False)
        finally:
            c.value += 3

    #:: ExpectedOutput(postcondition.violated:assertion.false)|ExpectedOutput(postcondition.violated:assertion.false, L1)
    def some_func_2(self, c: Container) -> int:
        Requires(Acc(c.value))
        Ensures(False)
        Exsures(MySpecialException, Acc(c.value) and c.value == Old(c.value) + 15)
        try:
            Super.other_func(self, c, True)
        except MySpecialException:
            Assert(False)
        finally:
            c.value += 3

    def other_func(self, c1: Container, b: bool) -> bool:
        Requires(Acc(c1.value))
        Ensures(Acc(c1.value) and c1.value == 99)
        Exsures(MyOtherException, Acc(c1.value) and c1.value == Old(c1.value) + 12)
        Exsures(MySpecialException, Acc(c1.value) and c1.value == Old(c1.value) + 7)
        # throw one exception, catch it
        try:
            if b:
                raise MySpecialException()
        except MyException:
            c1.value += 5
        try:
            if b:
                raise MyOtherException()
            else:
                raise MySpecialException()
        finally:
            c1.value += 7


#:: Label(L1)
class Sub(Super):
    def so_many_methods(self, ca: Container, cb: Container) -> Container:
        Requires(Acc(ca.value))
        Requires(Acc(cb.value))
        Ensures(Acc(Result().value) and Result().value == Old(cb.value) + 24)
        # call other
        try:
            Super.other_func(self, ca, False)
        except MySpecialException:
            ca.value = 77
        loc = Super.return_func(self, ca)
        Assert(loc == 77)
        try:
            Super.some_func(self, cb)
        except MyOtherException:
            cb.value += 9
        return cb

    def so_many_methods_2(self, ca: Container, cb: Container) -> Container:
        Requires(Acc(ca.value))
        Requires(Acc(cb.value))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Acc(Result().value) and Result().value == Old(cb.value) + 4)
        try:
            Super.other_func(self, ca, False)
        except MySpecialException:
            ca.value = 77
        loc = Super.return_func(self, ca)
        Assert(loc == 77)
        try:
            Super.some_func(self, cb)
        except MyOtherException:
            cb.value += 9
        return cb
