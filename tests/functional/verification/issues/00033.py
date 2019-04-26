# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def callee(a: int) -> int:
    return a * 2


def test2() -> None:
    a = callee(True)
