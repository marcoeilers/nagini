# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def test1() -> None:
    Requires(True)


def test2() -> None:
    Ensures(True)


def test3() -> None:
    Requires(True)
    Ensures(True)
