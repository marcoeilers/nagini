# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import Acc
from nagini_contracts.io_contracts import *


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
