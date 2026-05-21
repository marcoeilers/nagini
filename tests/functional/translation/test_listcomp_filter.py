# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def f(xs: List[int]) -> List[int]:
    Requires(Acc(list_pred(xs)))
    Ensures(Acc(list_pred(Result())))
    #:: ExpectedOutput(unsupported:Filter in list comprehension.)
    return [x for x in xs if x > 0]
