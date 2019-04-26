# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    def __init__(self) -> None:
        self.a = 12
        Ensures(Acc(self.a))
        Ensures(MayCreate(self, 'b'))

    def set(self) -> None:
        Requires(MayCreate(self, 'b'))
        self.b = 1212
        Ensures(Acc(self.b))

    def del1(self) -> None:
        Requires(Acc(self.b))
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Acc(self.b))
        del self.b

    def del2(self) -> None:
        Requires(Acc(self.b))
        Ensures(MayCreate(self, 'b'))
        del self.b

    def del3(self) -> None:
        Requires(Acc(self.b))
        Ensures(MaySet(self, 'b'))
        del self.b

    def del4(self) -> None:
        Requires(MaySet(self, 'b'))
        #:: ExpectedOutput(exhale.failed:insufficient.permission)
        del self.b

    def del5(self) -> None:
        Requires(MayCreate(self, 'b'))
        #:: ExpectedOutput(exhale.failed:insufficient.permission)
        del self.b


def client_7_1() -> None:
    a = A()
    a.b = 15
    a.del2()
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c = a.b

def client_7_2() -> None:
    a = A()
    a.b = 15
    a.del3()
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    c = a.b
