# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def f(xs: List[int]) -> None:
    Requires(Acc(list_pred(xs)))
    #:: ExpectedOutput(unsupported:enumerate only supported with single arg.)
    for i, x in enumerate(xs, 1):
        pass
