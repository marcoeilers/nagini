# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def method_with_loop() -> int:
    Ensures(Result() == 4 * 99)
    i = 0
    j = 99
    while j != 0:
        Invariant(i == 2 * (99 - j))
        i += 2
        j -= 1
    return i + 198


def invariant_not_preserved() -> int:
    Ensures(Result() == 4 * 99)
    i = 0
    j = 99
    while j != 0:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(i == 2 * (99 - j))
        i += 3
        j -= 1
    return i + 198


def invariant_not_established() -> int:
    Ensures(Result() == 4 * 99)
    i = -3
    j = 99
    while j != 0:
        #:: ExpectedOutput(invariant.not.established:assertion.false)
        Invariant(i == 2 * (99 - j))
        i += 2
        j -= 1
    return i + 198


def assertion_not_valid() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 4 * 99)
    i = 0
    j = 99
    while j != 0:
        Invariant(i == 2 * (99 - j))
        i += 2
        j -= 1
    return i


@Pure
def helper(a: int) -> bool:
    Ensures(Result() == (a != 5))
    return a != 5


def function_condition() -> int:
    Ensures(Result() == 10)
    i = 15
    sum = 0
    while helper(i):
        Invariant(sum == 15 - i)
        sum += 1
        i -= 1
    return sum


def nested_loop(arg: int) -> int:
    Ensures(Result() == (2 * arg) * 99)
    i = 0
    j = 99
    while j != 0:
        Invariant(i == (2 * arg) * (99 - j))
        toadd = 0
        ctr = 0
        while ctr != arg:
            Invariant(toadd == ctr * 2)
            toadd += 2
            ctr = ctr + 1
        i += toadd
        j -= 1
    return i


def nested_loop_fail(arg: int) -> int:
    Ensures(Result() == (2 * (arg + 1)) * 99)
    i = 0
    j = 99
    while j != 0:
        #:: ExpectedOutput(invariant.not.preserved:assertion.false)
        Invariant(i == (2 * arg) * (99 - j))
        toadd = 0
        ctr = 0
        while ctr != arg:
            Invariant(toadd == ctr * 3)
            toadd += 3
            ctr = ctr + 1
        i += toadd
        j -= 1
    return i + 198
