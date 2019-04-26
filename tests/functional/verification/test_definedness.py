# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class C:
    def __init__(self, b: bool) -> None:
        #:: ExpectedOutput(postcondition.violated:insufficient.permission)
        Ensures(Acc(self.argh))  # type: ignore
        self.urgh = 12
        if b:
            self.argh = object()


def double(a: int) -> int:
    if a > 0:
        u = 14
    #:: ExpectedOutput(expression.undefined:undefined.local.variable)
    uu = u
    return -a


def client() -> None:
    a = C(True)
