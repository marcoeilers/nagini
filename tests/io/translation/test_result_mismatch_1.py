from nagini_contracts.contracts import (
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *


@IOOperation
def test_io(
        t_pre: Place,
        value: int = Result()) -> bool:
    Terminates(True)


def test(t1: Place) -> None:
    #:: ExpectedOutput(invalid.program:invalid.io_operation_use.result_mismatch)
    Requires(test_io(t1))
