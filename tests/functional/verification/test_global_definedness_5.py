# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def foo_1() -> int:
    return const


def foo_2() -> int:
    return const2


class A:
    def __init__(self) -> None:
        foo_1()


class B:
    def __init__(self) -> None:
        foo_2()

const = 1

A()

#:: ExpectedOutput(assert.failed:assertion.false)
B()

const2 = 1