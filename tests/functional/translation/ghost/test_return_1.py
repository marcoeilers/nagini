# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def foo(i: int, gi: GInt) -> Tuple[int, GInt]:
    return i, gi

def bar(i: int, j: int) -> Tuple[int, GInt]:
    return i, j

def foobar() -> Tuple[int, GInt]:
    return 0, 0

def barfoo() -> Tuple[int, GInt]:
    i = 1
    gi: GInt = 2
    return i, gi