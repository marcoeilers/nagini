# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class A:
    def tester(self) -> bool:
        return True


def pred_acc(a: A) -> None:
    #:: ExpectedOutput(invalid.program:invalid.acc)
    Requires(Acc(a.tester()))
    return