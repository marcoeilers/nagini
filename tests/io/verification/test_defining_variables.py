# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    ContractOnly,
    Ensures,
    Requires,
    Result,
)
from nagini_contracts.io_contracts import *
from typing import Tuple, Callable


@ContractOnly
def test1() -> Place:
    IOExists1(Place)(
        lambda t2:
        Ensures(
            t2 == Result() and
            token(t2)
        )
    )


@ContractOnly
def test2() -> Place:
    IOExists1(Place)(
        lambda t2:
        Ensures(
            t2 == Result()
        )
    )


@ContractOnly
def test3() -> Tuple[Place, Place]:
    IOExists2(Place, Place)(
        lambda t2, t3:
        Ensures(
            t2 == Result()[0] and
            t3 == Result()[1]
        )
    )


@ContractOnly
def test4() -> Tuple[Place, Place, Place]:
    IOExists3(Place, Place, Place)(
        lambda t2, t3, t4:
        Ensures(
            t2 == Result()[0] and
            t3 == Result()[1] and
            t4 == Result()[2]
        )
    )


@ContractOnly
def test5() -> Tuple[Place, Place, Place]:
    IOExists3(Place, Place, Place)(
        lambda t2, t3, t4:
        Ensures(
            t2 == Result()[0] and
            # Check if also works with extra parenthesis.
            (t3 == Result()[1] and
            t4 == Result()[2])
        )
    )
