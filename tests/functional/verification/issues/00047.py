# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from typing import Tuple, List


def test() -> None:
    i = 1
    r = ['x']
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(Forall(r, lambda i: ('y' == i, [])))


@IOOperation
def read_io(
        t1: Place,
        result: str = Result(),
        t2: Place = Result()) -> bool:
    pass


@ContractOnly
def test_2(t1: Place, value: int) -> Tuple[str, Place]:
    Requires(value == 3)
    IOExists2(str, Place)(
        lambda value, t2: (
            Requires(
                token(t1) and
                read_io(t1, value, t2)
            ),
            Ensures(
                token(t2) and
                Result()[1] == t2 and
                Result()[0] == value
            ),
        )
    )
    Ensures(value == 4)
