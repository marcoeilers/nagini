# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


class E1(Exception):
    pass


class Coded(Exception):
    def __init__(self) -> None:
        self.code = 3
        Ensures(Acc(self.code) and self.code == 3)


def throw_coded() -> None:
    Ensures(False)
    Exsures(Coded, Acc(RaisedException().code) and RaisedException().code == 3)
    raise Coded()


# Each block appends a digit to c.val, so the value is the order they ran in.

@Inline
def return_through_finally(c: Cell, d: int) -> int:
    try:
        return d
    finally:
        c.val = c.val * 10 + d


@Inline
def raise_through_finally(c: Cell, d: int) -> None:
    try:
        raise E1()
    finally:
        c.val = c.val * 10 + d


@Inline
def return_in_loop(n: int) -> int:
    i = 0
    while i < n:
        Invariant(0 <= i and i <= n)
        if i == 3:
            return i
        i = i + 1
    return -1


@Inline
def catch_coded() -> int:
    try:
        throw_coded()
    except Coded as e:
        return e.code
    return 0


def inlined_twice(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 3)
    a = return_through_finally(c, 1)
    b = return_through_finally(c, 2)
    return a + b


def inlined_twice_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 21)
    a = return_through_finally(c, 1)
    b = return_through_finally(c, 2)
    return a + b


def inlined_in_try(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 1)
    try:
        return return_through_finally(c, 1)
    finally:
        c.val = c.val * 10 + 2


def inlined_raise_caught_by_caller(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 123 and Result() == 5)
    try:
        raise_through_finally(c, 1)
    except E1:
        c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3
    return 5


def inlined_raise_declared(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E1, Acc(c.val) and c.val == 1)
    raise_through_finally(c, 1)


def inlined_raise_declared_fail(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(E1, Acc(c.val) and c.val == 0)
    raise_through_finally(c, 1)


def inlined_raise_in_loop(c: Cell, n: int) -> int:
    Requires(Acc(c.val) and c.val == 0 and n >= 0)
    Ensures(Acc(c.val) and Result() == n)
    i = 0
    caught = 0
    while i < n:
        Invariant(Acc(c.val) and 0 <= i and i <= n and caught == i)
        try:
            i = i + 1
            raise_through_finally(c, 1)
        except E1:
            caught = caught + 1
    return caught


def inlined_return_in_loop(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == -1 or Result() == 3)
    r = return_in_loop(n)
    return r


def inlined_return_in_loop_fail(n: int) -> int:
    Requires(n >= 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == -1)
    r = return_in_loop(n)
    return r


def inlined_loop_in_loop_in_try(c: Cell, n: int) -> int:
    Requires(Acc(c.val) and c.val == 0 and n >= 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == n)
    i = 0
    try:
        while i < n:
            Invariant(Acc(c.val) and c.val == 0 and 0 <= i and i <= n)
            r = return_in_loop(i)
            i = i + 1
    finally:
        c.val = c.val * 10 + 1
    return i


def inlined_handler_variable() -> int:
    Ensures(Result() == 3)
    a = catch_coded()
    return a
