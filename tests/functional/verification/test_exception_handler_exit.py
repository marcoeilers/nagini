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


def thrower() -> None:
    Ensures(False)
    Exsures(E1, True)
    raise E1()


def quiet() -> None:
    Exsures(E1, False)


def return_in_handler(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 99 and Result() == 1)
    try:
        thrower()
    except E1:
        return 1
    finally:
        c.val = 99
    return 0


def return_in_handler_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 0)
    try:
        thrower()
    except E1:
        return 1
    finally:
        c.val = 99
    return 0


def raise_in_handler(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(E2, Acc(c.val) and c.val == 99)
    try:
        thrower()
    except E1:
        raise E2()
    finally:
        c.val = 99
    return 0


def raise_in_handler_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(E2, Acc(c.val) and c.val == 0)
    try:
        thrower()
    except E1:
        raise E2()
    finally:
        c.val = 99
    return 0


def raise_in_handler_passes_sibling() -> int:
    Ensures(False)
    Exsures(E2, True)
    try:
        thrower()
    except E1:
        raise E2()
    except E2:
        return 1
    return 0


def return_in_else(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 99 and Result() == 1)
    try:
        quiet()
    except E1:
        pass
    else:
        return 1
    finally:
        c.val = 99
    return 0


def handler_falls_through(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 99 and Result() == 2)
    x = 0
    try:
        thrower()
    except E1:
        x = 2
    finally:
        c.val = 99
    return x


def return_in_while_in_handler(c: Cell, n: int) -> int:
    Requires(Acc(c.val) and c.val == 0 and n >= 0)
    Ensures(Acc(c.val) and c.val == 99)
    Ensures(Result() == n or Result() == -1)
    i = 0
    try:
        thrower()
    except E1:
        while i < n:
            Invariant(0 <= i and i <= n)
            if i == 7:
                return -1
            i = i + 1
    finally:
        c.val = 99
    return i


def return_in_try_in_handler(c: Cell, d: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0 and Acc(d.val) and d.val == 0)
    Ensures(Acc(c.val) and c.val == 99 and Acc(d.val) and d.val == 98)
    Ensures(Result() == 1)
    try:
        thrower()
    except E1:
        try:
            return 1
        finally:
            d.val = 98
    finally:
        c.val = 99
    return 0


def break_in_handler(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 99)
    Ensures(Result() == 5)
    x = 0
    while True:
        Invariant(Acc(c.val))
        try:
            thrower()
        except E1:
            break
        finally:
            c.val = 99
    x = 5
    return x


class MyException(Exception):
    def __init__(self) -> None:
        self.code = 3
        Ensures(Acc(self.code) and self.code == 3)


def coded_thrower() -> None:
    Ensures(False)
    Exsures(MyException, Acc(RaisedException().code) and RaisedException().code == 3)
    raise MyException()


def call_in_handler() -> int:
    Ensures(Result() == 3)
    try:
        coded_thrower()
    except MyException as e:
        quiet()
        return e.code
    return 0


def call_and_reraise_in_handler() -> int:
    Ensures(False)
    Exsures(MyException, Acc(RaisedException().code) and RaisedException().code == 3)
    try:
        coded_thrower()
    except MyException as e:
        quiet()
        raise e
    return 0


def caught_by_outer_handler() -> int:
    Ensures(Result() == 3)
    try:
        try:
            coded_thrower()
        except E2:
            pass
    except MyException as e:
        return e.code
    return 0


def caught_by_outer_handler_after_finally() -> int:
    Ensures(Result() == 3)
    x = 0
    try:
        try:
            coded_thrower()
        finally:
            x = 1
    except MyException as e:
        return e.code
    return 0


def raised_through_outer_finally() -> int:
    Ensures(False)
    Exsures(MyException, Acc(RaisedException().code) and RaisedException().code == 3)
    x = 0
    try:
        try:
            coded_thrower()
        except E2:
            pass
    finally:
        x = 1
    return 0


class Manager:
    def __init__(self, c: Cell) -> None:
        self.c = c
        Ensures(Acc(self.c) and self.c is c)

    def __enter__(self) -> 'Manager':
        return self

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        Requires(Acc(self.c, 1/2) and Acc(self.c.val))
        Ensures(Acc(self.c, 1/2) and Acc(self.c.val) and self.c.val == 99)
        Ensures(Result() == (t is None))
        self.c.val = 99
        return t is None


def with_in_try(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 99 and Result() == 1)
    m = Manager(c)
    try:
        with m:
            thrower()
    except E1:
        return 1
    return 0


def with_in_try_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 0)
    m = Manager(c)
    try:
        with m:
            thrower()
    except E1:
        return 1
    return 0


def try_in_with(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 99 and Result() == 1)
    m = Manager(c)
    x = 0
    with m:
        try:
            return 1
        finally:
            x = 1
    return 0


def try_in_with_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 0)
    m = Manager(c)
    x = 0
    with m:
        try:
            return 1
        finally:
            x = 1
    return 0


def raising_step(i: int) -> int:
    Ensures(Result() == i + 1)
    Exsures(E2, i < 0)
    if i < 0:
        raise E2()
    return i + 1


def raising_loop_in_handler(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == 3)
    Exsures(E2, False)
    i = 0
    x = 0
    try:
        coded_thrower()
    except MyException as e:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = raising_step(i)
        return e.code
    finally:
        x = 1
    return 0


class Derived(MyException):
    pass


class OtherException(Exception):
    def __init__(self) -> None:
        self.code = 4
        Ensures(Acc(self.code) and self.code == 4)


def other_thrower() -> None:
    Ensures(False)
    Exsures(OtherException, Acc(RaisedException().code) and RaisedException().code == 4)
    raise OtherException()


def supertype_handler_catches_subtype() -> int:
    Ensures(Result() == 1)
    try:
        raise Derived()
    except MyException:
        return 1
    return 0


def first_matching_handler_wins() -> int:
    Ensures(Result() == 1)
    try:
        raise Derived()
    except MyException:
        return 1
    except Derived:
        return 2
    return 0


def subtype_handler_skips_supertype() -> int:
    Ensures(Result() == 2)
    try:
        raise MyException()
    except Derived:
        return 1
    except MyException:
        return 2
    return 0


def subtype_handler_skips_supertype_fail() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 1)
    try:
        raise MyException()
    except Derived:
        return 1
    except MyException:
        return 2
    return 0


# Each block appends a digit to c.val, so the value is the order they ran in.

def unmatched_passes_handler_and_finally(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 23 and Result() == 4)
    try:
        try:
            thrower()
        except E2:
            c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    except E1:
        c.val = c.val * 10 + 3
        return 4
    return 0


def raise_in_handler_caught_by_outer(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 4)
    try:
        try:
            thrower()
        except E1:
            raise E2()
        finally:
            c.val = c.val * 10 + 1
    except E2:
        c.val = c.val * 10 + 2
        return 4
    return 0


def raise_in_else_passes_own_handlers(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 4)
    try:
        try:
            quiet()
        except E1:
            c.val = c.val * 10 + 9
        else:
            thrower()
        finally:
            c.val = c.val * 10 + 1
    except E1:
        c.val = c.val * 10 + 2
        return 4
    return 0


def raise_in_else_passes_own_handlers_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 91)
    try:
        try:
            quiet()
        except E1:
            c.val = c.val * 10 + 9
        else:
            thrower()
        finally:
            c.val = c.val * 10 + 1
    except E1:
        return 4
    return 0


def else_then_finally(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 123)
    try:
        quiet()
        c.val = c.val * 10 + 1
    except E1:
        c.val = c.val * 10 + 9
    else:
        c.val = c.val * 10 + 2
    finally:
        c.val = c.val * 10 + 3


def handler_variable_after_try_in_handler() -> int:
    Ensures(Result() == 3)
    try:
        coded_thrower()
    except MyException as e:
        try:
            thrower()
        except E1:
            pass
        return e.code
    return 0


def same_handler_variable_twice() -> int:
    Ensures(Result() == 7)
    x = 0
    try:
        coded_thrower()
    except MyException as e:
        x = e.code
    try:
        other_thrower()
    except OtherException as e:
        x = x + e.code
    return x


def two_handler_variables() -> int:
    Ensures(Result() == 34)
    try:
        coded_thrower()
    except MyException as e:
        try:
            other_thrower()
        except OtherException as f:
            return e.code * 10 + f.code
    return 0


def reraise_through_finally(c: Cell) -> None:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(False)
    Exsures(MyException, Acc(c.val) and c.val == 1)
    Exsures(MyException, Acc(RaisedException().code) and RaisedException().code == 3)
    try:
        coded_thrower()
    except MyException as e:
        raise e
    finally:
        c.val = c.val * 10 + 1


#:: ExpectedOutput(exhale.failed:assertion.false)
def undeclared_exception_after_finally_fail(c: Cell) -> None:
    Requires(Acc(c.val))
    Ensures(Acc(c.val))
    try:
        thrower()
    finally:
        c.val = 1
