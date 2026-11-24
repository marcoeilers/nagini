# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List, Optional

from nagini_contracts.contracts import *


class MyException(Exception):
    pass


def step(i: int) -> int:
    Ensures(Result() == i + 1)
    Exsures(MyException, i < 0)
    if i < 0:
        raise MyException()
    return i + 1


class Manager:
    def __init__(self) -> None:
        pass

    def __enter__(self) -> 'Manager':
        return self

    def __exit__(self, t: object, e: object, tb: object) -> bool:
        return t is None


def raise_in_while_in_finally(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    Exsures(MyException, False)
    i = 0
    done = 0
    try:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = step(i)
    finally:
        done = 1
    return i


def raise_in_for_in_finally(xs: List[int]) -> int:
    Requires(Acc(list_pred(xs)))
    Ensures(Result() == 1)
    Exsures(MyException, False)
    done = 0
    try:
        for x in xs:
            y = step(0)
    finally:
        done = 1
    return done


def raise_in_while_in_nested_finally(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    Exsures(MyException, False)
    i = 0
    a = 0
    b = 0
    try:
        try:
            while i < n:
                Invariant(0 <= i and i <= n)
                i = step(i)
        finally:
            a = 1
    finally:
        b = 1
    return i


def raise_in_while_in_with(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    Exsures(MyException, False)
    i = 0
    m = Manager()
    with m:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = step(i)
    return i


def return_in_while_in_finally(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n or Result() == -1)
    i = 0
    done = 0
    try:
        while i < n:
            Invariant(0 <= i and i <= n)
            if i == 7:
                return -1
            i = i + 1
    finally:
        done = 1
    return i


def return_in_for_in_finally(xs: List[int]) -> int:
    Requires(Acc(list_pred(xs)))
    Ensures(Result() == 1 or Result() == -1)
    done = 0
    try:
        for x in xs:
            if x == 7:
                return -1
    finally:
        done = 1
    return done


def return_in_while_in_with(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n or Result() == -1)
    i = 0
    m = Manager()
    with m:
        while i < n:
            Invariant(0 <= i and i <= n)
            if i == 7:
                return -1
            i = i + 1
    return i


def break_in_while_in_finally() -> int:
    Ensures(Result() == 5)
    x = 0
    try:
        while True:
            break
        x = 5
    finally:
        pass
    return x


def break_in_while_in_finally_fail() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 0)
    x = 0
    try:
        while True:
            break
        x = 5
    finally:
        pass
    return x


def continue_in_while_in_finally(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == 5)
    i = 0
    x = 0
    try:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = i + 1
            continue
        x = 5
    finally:
        pass
    return x


def while_in_finally_after_return(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == 5)
    i = 0
    try:
        return 5
    finally:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = i + 1


def while_in_finally_after_return_fail(n: int) -> Optional[int]:
    Requires(n >= 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() is None)
    i = 0
    try:
        return 5
    finally:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = i + 1


def return_before_nested_while(n: int) -> None:
    Exsures(MyException, True)
    i = 0
    while i < n:
        if i == 5:
            return
        j = 0
        while j < i:
            j += 1
        i += 1


def return_value_before_nested_for(xs: List[int], ys: List[int]) -> int:
    Requires(Acc(list_pred(xs)) and Acc(list_pred(ys)))
    Ensures(Result() == 0 or Result() == 7)
    Exsures(MyException, True)
    for x in xs:
        Invariant(Acc(list_pred(ys)))
        if x == 7:
            return x
        for y in ys:
            pass
    return 0


class Pending(Exception):
    pass


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


# Each block appends a digit to c.val, so the value is the order they ran in.

def break_through_two_finally_blocks(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 123 and Result() == 5)
    while True:
        Invariant(Acc(c.val) and c.val == 0)
        try:
            try:
                break
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    c.val = c.val * 10 + 3
    return 5


def break_through_two_finally_blocks_fail(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 3)
    while True:
        Invariant(Acc(c.val) and c.val == 0)
        try:
            try:
                break
            finally:
                c.val = c.val * 10 + 1
        finally:
            c.val = c.val * 10 + 2
    c.val = c.val * 10 + 3
    return 5


def continue_through_finally(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    i = 0
    done = 0
    while i < n:
        Invariant(0 <= i and i <= n and done == i)
        try:
            i = i + 1
            continue
        finally:
            done = done + 1
    return done


def continue_in_for_through_finally(xs: List[int]) -> int:
    Requires(Acc(list_pred(xs)))
    Ensures(Result() == 0)
    reached = 0
    for x in xs:
        Invariant(reached == 0)
        try:
            if x > 0:
                continue
        finally:
            pass
        if x > 0:
            reached = 1
    return reached


def break_in_for_through_finally(xs: List[int]) -> int:
    Requires(Acc(list_pred(xs)))
    Ensures(Result() == 0 or Result() == 1)
    seen = 0
    for x in xs:
        Invariant(seen == 0)
        try:
            break
        finally:
            seen = 1
    return seen


def break_in_for_through_finally_fail(xs: List[int]) -> int:
    Requires(Acc(list_pred(xs)))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 0)
    seen = 0
    for x in xs:
        Invariant(seen == 0)
        try:
            break
        finally:
            seen = 1
    return seen


def break_leaves_inner_loop_only(c: Cell, n: int) -> int:
    Requires(Acc(c.val) and c.val == 0 and n >= 0)
    Ensures(Acc(c.val) and c.val == n + 100 and Result() == n)
    i = 0
    try:
        while i < n:
            Invariant(Acc(c.val) and c.val == i and 0 <= i and i <= n)
            while True:
                Invariant(Acc(c.val) and c.val == i)
                try:
                    break
                finally:
                    c.val = c.val + 1
            i = i + 1
    finally:
        c.val = c.val + 100
    return i


def loop_else_skipped_by_break_through_finally(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 5)
    i = 0
    while i < 3:
        Invariant(Acc(c.val) and c.val == 0 and i == 0)
        try:
            break
        finally:
            c.val = c.val * 10 + 1
    else:
        c.val = c.val * 10 + 9
    return 5


def loop_else_after_continue_through_finally(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 5)
    i = 0
    while i < 1:
        Invariant(Acc(c.val) and c.val == i and 0 <= i and i <= 1)
        try:
            i = i + 1
            continue
        finally:
            c.val = c.val + 1
    else:
        c.val = c.val * 10 + 2
    return 5


def exception_handled_in_each_iteration(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    i = 0
    caught = 0
    while i < n:
        Invariant(0 <= i and i <= n and caught == i)
        try:
            i = i + 1
            raise MyException()
        except MyException:
            caught = caught + 1
    return caught


def raise_in_loop_caught_outside(n: int) -> int:
    Requires(n > 3)
    Ensures(Result() == 3)
    i = 0
    try:
        while i < n:
            Invariant(0 <= i and i <= 3)
            if i == 3:
                raise MyException()
            i = i + 1
    except MyException:
        return i
    return -1


def break_in_handler_in_loop_in_try(c: Cell) -> int:
    Requires(Acc(c.val) and c.val == 0)
    Ensures(Acc(c.val) and c.val == 12 and Result() == 5)
    try:
        while True:
            Invariant(Acc(c.val) and c.val == 0)
            try:
                raise MyException()
            except MyException:
                break
        c.val = c.val * 10 + 1
    finally:
        c.val = c.val * 10 + 2
    return 5


def return_in_nested_loops_in_try(c: Cell, n: int) -> int:
    Requires(Acc(c.val) and c.val == 0 and n > 0)
    Ensures(Acc(c.val) and c.val == 1 and Result() == 7)
    i = 0
    try:
        while i < n:
            Invariant(Acc(c.val) and c.val == 0 and i == 0)
            j = 0
            while j < n:
                Invariant(j == 0)
                return 7
            i = i + 1
    finally:
        c.val = c.val * 10 + 1
    return 0


def loop_in_finally_keeps_exception(c: Cell, n: int) -> None:
    Requires(Acc(c.val) and c.val == 0 and n >= 0)
    Ensures(False)
    Exsures(Pending, Acc(c.val) and c.val == n)
    try:
        raise Pending()
    finally:
        while c.val < n:
            Invariant(Acc(c.val) and 0 <= c.val and c.val <= n)
            c.val = c.val + 1


def raising_loop_in_finally_keeps_return(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == 5)
    Exsures(MyException, False)
    i = 0
    try:
        return 5
    finally:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = step(i)


def raising_loop_in_finally_keeps_exception(n: int) -> None:
    Requires(n >= 0)
    Ensures(False)
    Exsures(Pending, True)
    Exsures(MyException, False)
    i = 0
    try:
        raise Pending()
    finally:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = step(i)


def raising_loop_in_finally_keeps_exception_fail(n: int) -> None:
    Requires(n >= 0)
    Exsures(MyException, True)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Exsures(Pending, False)
    i = 0
    try:
        raise Pending()
    finally:
        while i < n:
            Invariant(0 <= i and i <= n)
            i = step(i)


def return_in_loop_in_finally(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == (-1 if n > 7 else 5))
    i = 0
    try:
        return 5
    finally:
        while i < n:
            Invariant(0 <= i and i <= n and i <= 7)
            if i == 7:
                return -1
            i = i + 1


def discarded_return_in_finally() -> int:
    Ensures(Result() == 1)
    try:
        return 1
    finally:
        while True:
            try:
                return 2
            finally:
                break


def discarded_return_in_finally_fail() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 2)
    try:
        return 1
    finally:
        while True:
            try:
                return 2
            finally:
                break


def loop_in_finally_in_loop(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    i = 0
    total = 0
    while i < n:
        Invariant(0 <= i and i <= n and total == i)
        try:
            i = i + 1
            continue
        finally:
            j = 0
            while j < 3:
                Invariant(0 <= j and j <= 3)
                j = j + 1
            total = total + 1
    return total


def raising_loop_in_finally_in_loop(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    Exsures(MyException, False)
    i = 0
    total = 0
    while i < n:
        Invariant(0 <= i and i <= n and total == i)
        try:
            i = i + 1
            continue
        finally:
            j = 0
            while j < 3:
                Invariant(0 <= j and j <= 3)
                j = step(j)
            total = total + 1
    return total
