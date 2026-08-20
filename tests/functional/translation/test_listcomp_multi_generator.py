# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def f(xs: List[int], ys: List[int]) -> List[int]:
    Requires(Acc(list_pred(xs)) and Acc(list_pred(ys)))
    Ensures(Acc(list_pred(Result())))
    #:: ExpectedOutput(unsupported:Multiple generators in list comprehension.)
    return [x + y for x in xs for y in ys]
