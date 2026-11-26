# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class MyException(Exception):
    pass


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


def return_value_before_nested_while(n: int) -> int:
    Ensures(Result() == 0 or Result() == 5)
    Exsures(MyException, True)
    i = 0
    while i < n:
        if i == 5:
            return i
        j = 0
        while j < i:
            j += 1
        i += 1
    return 0
