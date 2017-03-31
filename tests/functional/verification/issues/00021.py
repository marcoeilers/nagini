from nagini_contracts.contracts import *


def test1() -> None:
    Requires(True)


def test2() -> None:
    Ensures(True)


def test3() -> None:
    Requires(True)
    Ensures(True)
