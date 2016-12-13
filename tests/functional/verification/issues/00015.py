from py2viper_contracts.contracts import *


class C:
    pass


class A(C):
    def a(self) -> int:
        return 1


class B(C):
    def b(self) -> int:
        return 2


#:: ExpectedOutput(postcondition.violated:assertion.false)
def test(c: C) -> int:
    Requires(c is not None)
    if (isinstance(c, A) and c.a() == 1) or (isinstance(c, B) and c.b() == 2):
        return 1
