from nagini_contracts.contracts import *

class A:
    def tester(self) -> bool:
        return True


def pred_acc(a: A) -> None:
    #:: ExpectedOutput(invalid.program:invalid.acc)
    Requires(Acc(a.tester()))
    return