from nagini_contracts.contracts import *

def foo_1() -> int:
    Requires(Acc(const))
    Ensures(Acc(const))
    global const
    const += 1
    return const


def foo_2() -> int:
    Requires(Acc(const2))
    Ensures(Acc(const2))
    global const2
    const2 += 1
    return const2


class A:
    def __init__(self) -> None:
        Requires(Acc(const))
        Ensures(Acc(const))
        foo_1()


class B:
    def __init__(self) -> None:
        Requires(Acc(const2))
        Ensures(Acc(const2))
        foo_2()

const = 1

A()


# deps
#:: ExpectedOutput(assert.failed:assertion.false)
B()

const2 = 1