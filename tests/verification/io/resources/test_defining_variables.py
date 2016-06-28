from py2viper_contracts.contracts import Requires, Ensures
from py2viper_contracts.io import *
from typing import Tuple, Callable


def test1() -> Place:
    IOExists1(Place)(
        lambda t2:
        Ensures(
            t2 == Result() and
            token(t2)
        )
    )


def test2() -> Place:
    IOExists1(Place)(
        lambda t2:
        Ensures(
            t2 == Result()
        )
    )


def test3() -> Tuple[Place, Place]:
    IOExists2(Place, Place)(
        lambda t2, t3:
        Ensures(
            t2 == Result()[0] and
            t3 == Result()[1]
        )
    )


def test4() -> Tuple[Place, Place, Place]:
    IOExists3(Place, Place, Place)(
        lambda t2, t3, t4:
        Ensures(
            t2 == Result()[0] and
            t3 == Result()[1] and
            t4 == Result()[2]
        )
    )


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
