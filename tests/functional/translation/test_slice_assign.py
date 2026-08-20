# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def f(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)) and len(xs) >= 3)
    Ensures(Acc(list_pred(xs)))
    #:: ExpectedOutput(unsupported:assignment to slice)
    xs[1:3] = [10, 20]
