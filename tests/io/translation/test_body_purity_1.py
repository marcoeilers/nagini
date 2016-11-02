from py2viper_contracts.contracts import Acc
from py2viper_contracts.io import *


class C:

    def __init__(self) -> None:
        self.f = 1


@IOOperation
def test_io(
        t_pre: Place,
        x: C,
        ) -> bool:
    Terminates(True)
    #:: ExpectedOutput(invalid.program:invalid.io_operation.body.non_pure)
    return Acc(x.f)
