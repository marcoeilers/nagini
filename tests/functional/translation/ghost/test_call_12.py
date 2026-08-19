# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def var_args(*args: int) -> int:
    return 0

def two_args(a: int, b: int) -> int:
    return a + b

def calls(i: int, t: Tuple[int, int]) -> int:
    x = var_args(i, i, i)
    y = two_args(*t)
    return x + y
