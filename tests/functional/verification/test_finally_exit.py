# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


class E1(Exception):
    pass


class E2(Exception):
    pass


class Coded(Exception):
    def __init__(self) -> None:
        self.code = 3
        Ensures(Acc(self.code) and self.code == 3)


def throw1() -> None:
    Ensures(False)
    Exsures(E1, True)
    raise E1()


def throw_coded() -> None:
    Ensures(False)
    Exsures(Coded, Acc(RaisedException().code) and RaisedException().code == 3)
    raise Coded()


def quiet() -> None:
    Exsures(E1, False)


# Each block appends a digit to c.val, so the value is the order they ran in.

def return_runs_finally_blocks_inside_out(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 123 and Result() == 7)
    try:
        try:
            try:
                return 7
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3


def return_runs_finally_blocks_inside_out_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 321)
    try:
        try:
            try:
                return 7
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3


def raise_runs_finally_blocks_inside_out(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E1, Acc(c.val) and c.val == 123)
    try:
        try:
            try:
                throw1()
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3


def raise_runs_finally_blocks_inside_out_fail(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(E1, Acc(c.val) and c.val == 12)
    try:
        try:
            try:
                throw1()
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3


def normal_runs_finally_blocks_inside_out(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 4123)
    try:
        try:
            try:
                c.val = 4
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3


def finally_handler_finally(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1234 and Result() == 5)
    try:
        try:
            try:
                throw1()
            finally:
                c.val = c.val * 10 + 1
        except E1:
            c.val = c.val * 10 + 2
        finally:
            c.val = c.val * 10 + 3
    finally:
        c.val = c.val * 10 + 4
    return 5


# What a finally block does while a return or an exception is pending.

def try_in_finally_keeps_return(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 1)
    try:
        return 1
    finally:
        try:
            throw1()
        except E1:
            c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2


def try_in_finally_keeps_exception(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E1, Acc(c.val) and c.val == 12)
    Exsures(E2, False)
    try:
        throw1()
    finally:
        try:
            raise E2()
        except E2:
            c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2


def try_in_finally_keeps_exception_fail(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Exsures(E2, True)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(E1, False)
    try:
        throw1()
    finally:
        try:
            raise E2()
        except E2:
            c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2


def call_in_finally_keeps_exception(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E1, Acc(c.val) and c.val == 1)
    try:
        throw1()
    finally:
        quiet()
        c.val = c.val * 10 + 1


def call_in_finally_keeps_exception_for_handler(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 3)
    try:
        try:
            throw_coded()
        finally:
            quiet()
            c.val = c.val * 10 + 1
    except Coded as e:
        return e.code
    return 0


def call_in_finally_keeps_return(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 7)
    Exsures(E1, False)
    try:
        return 7
    finally:
        quiet()
        c.val = c.val * 10 + 1


# An exit from a finally block replaces the pending one.

def raise_in_finally_replaces_exception() -> None:
    Ensures(False)
    Exsures(E2, True)
    Exsures(E1, False)
    try:
        throw1()
    finally:
        raise E2()


def raise_in_finally_replaces_exception_fail() -> None:
    Ensures(False)
    Exsures(E1, True)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(E2, False)
    try:
        throw1()
    finally:
        raise E2()


def raise_in_finally_replaces_return() -> int:
    Ensures(False)
    Exsures(E2, True)
    try:
        return 1
    finally:
        raise E2()


def raise_in_finally_caught_outside(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 3)
    try:
        try:
            return 1
        finally:
            c.val = c.val * 10 + 1
            throw1()
    except E1:
        c.val = c.val * 10 + 2
        return 3


def return_in_finally_replaces_return() -> int:
    Ensures(Result() == 2)
    try:
        return 1
    finally:
        return 2


def return_in_finally_replaces_return_fail() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 1)
    try:
        return 1
    finally:
        return 2


def return_in_finally_swallows_exception() -> int:
    Ensures(Result() == 2)
    try:
        throw1()
    finally:
        return 2


def break_in_finally_replaces_return() -> int:
    Ensures(Result() == 2)
    while True:
        try:
            return 1
        finally:
            break
    return 2


def break_in_finally_swallows_exception() -> int:
    Ensures(Result() == 2)
    while True:
        try:
            throw1()
        finally:
            break
    return 2


# A with block is left like a try block with a finally block. The exit method
# appends d to c.val, or 9 where it is given an exception.

class Manager:
    def __init__(self, c: Cell, d: int) -> None:
        self.c = c
        self.d = d
        Ensures(Acc(self.c) and self.c is c and Acc(self.d) and self.d == d)

    def __enter__(self) -> 'Manager':
        return self

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        Requires(Acc(self.c, 1/2) and Acc(self.d, 1/2) and Acc(self.c.val))
        Ensures(Acc(self.c, 1/2) and Acc(self.d, 1/2) and Acc(self.c.val))
        Ensures(self.c.val == Old(self.c.val) * 10 + (self.d if e is None else 9))
        self.c.val = self.c.val * 10 + (self.d if e is None else 9)
        return e is None


def nested_with_exits_inside_out(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 5)
    outer = Manager(c, 2)
    inner = Manager(c, 1)
    with outer:
        with inner:
            return 5


def nested_with_exits_inside_out_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 21)
    outer = Manager(c, 2)
    inner = Manager(c, 1)
    with outer:
        with inner:
            return 5


def raise_in_nested_with(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E1, Acc(c.val) and c.val == 99)
    outer = Manager(c, 2)
    inner = Manager(c, 1)
    with outer:
        with inner:
            throw1()


def normal_exit_of_with(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 5)
    m = Manager(c, 1)
    with m:
        pass
    return 5


def break_in_with(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 5)
    m = Manager(c, 1)
    while True:
        Invariant(Acc(m.c) and m.c is c and Acc(m.d) and m.d == 1)
        Invariant(Acc(c.val) and c.val == 0)
        with m:
            break
    return 5


def continue_in_with(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 1)
    m = Manager(c, 1)
    i = 0
    while i < 1:
        Invariant(Acc(m.c) and m.c is c and Acc(m.d) and m.d == 1)
        Invariant(Acc(c.val) and c.val == i and 0 <= i and i <= 1)
        i = i + 1
        with m:
            continue
    return i


def with_in_finally_keeps_return(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 7)
    m = Manager(c, 1)
    try:
        return 7
    finally:
        with m:
            pass


def handler_in_with(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 5)
    m = Manager(c, 1)
    with m:
        try:
            throw1()
        except E1:
            return 5
    return 0
