# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


class Whatever:
    pass


def something(normal: int, named1: bool, named2: object,
              named_default: int = 13,
              named_default2: Tuple[int, bool]=(2, True)) -> int:
    Ensures(Result() == named_default2[0])
    return named_default2[0]


def caller() -> int:
    Ensures(Result() == 12)
    #:: ExpectedOutput(type.error:Unexpected keyword argument "named3" for "something")
    r = something(23, False, named_default2=(12, False), named2=Whatever(),
                  named3=456)
    return r
