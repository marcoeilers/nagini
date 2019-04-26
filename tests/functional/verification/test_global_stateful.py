# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

b = 12
a = [b]  # type: List[int]


def foo() -> None:
    Requires(Acc(list_pred(a)) and len(a) < 2)
    Ensures(Acc(list_pred(a)))
    Ensures(len(a) == Old(len(a)) + 1)
    a.append(1)


foo()

#:: ExpectedOutput(call.precondition:assertion.false)
foo()