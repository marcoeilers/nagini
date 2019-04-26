# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class MyException(Exception):
    def __init__(self) -> None:
        self.f1 = 0
        Ensures(Acc(self.f1) and self.f1 == 0)


class OtherException(Exception):
    def __init__(self) -> None:
        self.f2 = 0
        Ensures(Acc(self.f2) and self.f2 == 0)


def success(b: bool) -> None:
    Exsures(MyException, Acc(RaisedException().f1) and RaisedException().f1 == 4)
    Exsures(OtherException, Acc(RaisedException().f2) and RaisedException().f2 == 5)
    if b:
        e = MyException()
        e.f1 = 4
        raise e
    else:
        e2 = OtherException()
        e2.f2 = 5
        raise e2


def fail(b: bool) -> None:
    Exsures(MyException, Acc(RaisedException().f1) and RaisedException().f1 == 4)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(OtherException, Acc(RaisedException().f2) and RaisedException().f2 == 6)
    if b:
        e = MyException()
        e.f1 = 4
        raise e
    else:
        e2 = OtherException()
        e2.f2 = 5
        raise e2