# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Optional

from nagini_contracts.contracts import *


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


class E1(Exception):
    pass


class E2(Exception):
    pass


def throw2() -> None:
    Ensures(False)
    Exsures(E2, True)
    raise E2()


class Manager:
    def __init__(self, c: Cell) -> None:
        self.c = c
        Ensures(Acc(self.c) and self.c is c)

    def __enter__(self) -> 'Manager':
        return self

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        Requires(Acc(self.c, 1/2) and Acc(self.c.val))
        Ensures(Acc(self.c, 1/2) and Acc(self.c.val))
        Ensures(self.c.val == Old(self.c.val) * 10 + (1 if e is None else 9))
        self.c.val = self.c.val * 10 + (1 if e is None else 9)
        return e is None


class Swallow:
    def __enter__(self) -> 'Swallow':
        return self

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        Ensures(Result())
        return True


def break_leaves_only_the_loop() -> int:
    Ensures(Result() == 5)
    r = 0
    try:
        while True:
            break
        r = 5
    finally:
        pass
    return r


def break_leaves_only_the_loop_wrong() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 0)
    r = 0
    try:
        while True:
            break
        r = 5
    finally:
        pass
    return r


def loop_in_finally_keeps_return() -> Optional[int]:
    Ensures(Result() is not None and Result() == 5)
    try:
        return 5
    finally:
        i = 0
        while i < 1:
            i = i + 1


def loop_in_finally_keeps_return_wrong() -> Optional[int]:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() is None)
    try:
        return 5
    finally:
        i = 0
        while i < 1:
            i = i + 1


def return_in_handler_runs_finally(c: Cell) -> int:
    Requires(Acc(c.val))
    Ensures(Acc(c.val) and c.val == 1 and Result() == 1)
    Exsures(E1, False)
    c.val = 0
    try:
        raise E1()
    except E1:
        return 1
    finally:
        c.val = 1


def return_in_handler_runs_finally_wrong(c: Cell) -> int:
    Requires(Acc(c.val))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 0)
    c.val = 0
    try:
        raise E1()
    except E1:
        return 1
    finally:
        c.val = 1


def caught_exception_runs_exit(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 9)
    m = Manager(c)
    try:
        with m:
            raise E1()
    except E1:
        pass


def caught_exception_runs_exit_wrong(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 0)
    m = Manager(c)
    try:
        with m:
            raise E1()
    except E1:
        pass


def return_through_finally_runs_exit(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 1)
    m = Manager(c)
    with m:
        try:
            return 1
        finally:
            pass


def return_through_finally_runs_exit_wrong(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 0)
    m = Manager(c)
    with m:
        try:
            return 1
        finally:
            pass


def finally_keeps_pending_exception(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E1, Acc(c.val) and c.val == 2)
    try:
        raise E1()
    finally:
        i = 0
        while i < 2:
            Invariant(Acc(c.val) and 0 <= i and i <= 2 and c.val == i)
            try:
                throw2()
            except E2:
                c.val = c.val + 1
            i = i + 1


def finally_keeps_pending_exception_wrong(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(E1, Acc(c.val) and c.val == 3)
    try:
        raise E1()
    finally:
        i = 0
        while i < 2:
            Invariant(Acc(c.val) and 0 <= i and i <= 2 and c.val == i)
            try:
                throw2()
            except E2:
                c.val = c.val + 1
            i = i + 1


def raise_in_else_skips_own_handler(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 23)
    Exsures(E1, False)
    try:
        try:
            try:
                pass
            except E1:
                c.val = c.val * 10 + 1
            else:
                raise E1()
            finally:
                c.val = c.val * 10 + 2
        except E1:
            c.val = c.val * 10 + 3
    except E1:
        c.val = c.val * 10 + 4


def raise_in_else_skips_own_handler_wrong(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 24)
    Exsures(E1, False)
    try:
        try:
            try:
                pass
            except E1:
                c.val = c.val * 10 + 1
            else:
                raise E1()
            finally:
                c.val = c.val * 10 + 2
        except E1:
            c.val = c.val * 10 + 3
    except E1:
        c.val = c.val * 10 + 4


def break_and_continue_run_exit(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 11)
    m = Manager(c)
    i = 0
    while True:
        Invariant(Acc(m.c) and m.c is c and Acc(c.val))
        Invariant((i == 0 and c.val == 0) or (i == 1 and c.val == 1))
        i = i + 1
        with m:
            if i == 1:
                continue
            break


def break_and_continue_run_exit_wrong(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 1)
    m = Manager(c)
    i = 0
    while True:
        Invariant(Acc(m.c) and m.c is c and Acc(c.val))
        Invariant((i == 0 and c.val == 0) or (i == 1 and c.val == 1))
        i = i + 1
        with m:
            if i == 1:
                continue
            break


def exit_swallows_exception() -> int:
    Ensures(Result() == 1)
    m = Swallow()
    with m:
        raise E1()
    return 1


def exit_swallows_exception_wrong() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    Exsures(E1, True)
    m = Swallow()
    with m:
        raise E1()
    return 1
