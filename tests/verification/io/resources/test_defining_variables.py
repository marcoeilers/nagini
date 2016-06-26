from py2viper_contracts.contracts import Requires, Ensures
from py2viper_contracts.io import *
from typing import Tuple, Callable


def test1() -> Place:
    IOExists = lambda t2: (
        Ensures(
            t2 == Result() and
            token(t2)
        )
    )   # type: Callable[[Place], bool]


def test2() -> Place:
    IOExists = lambda t2: (
        Ensures(
            t2 == Result()
        )
    )   # type: Callable[[Place], bool]


def test3() -> Tuple[Place, Place]:
    IOExists = lambda t2, t3: (
        Ensures(
            t2 == Result()[0] and
            t3 == Result()[1]
        )
    )   # type: Callable[[Place, Place], bool]


def test4() -> Tuple[Place, Place, Place]:
    IOExists = lambda t2, t3, t4: (
        Ensures(
            t2 == Result()[0] and
            t3 == Result()[1] and
            t4 == Result()[2]
        )
    )   # type: Callable[[Place, Place, Place], bool]


def test5() -> Tuple[Place, Place, Place]:
    IOExists = lambda t2, t3, t4: (
        Ensures(
            t2 == Result()[0] and
            (t3 == Result()[1] and
            t4 == Result()[2])
        )
    )   # type: Callable[[Place, Place, Place], bool]
