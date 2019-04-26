# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

@Pure
def odd_sum_rec(l: List[int], end: int) -> int:
    Requires(Acc(list_pred(l), 1/2))
    Requires(end >= -1 and end < len(l))
    if end == -1:
        return 0
    else:
        before = odd_sum_rec(l, end - 1)
        if l[end] % 2 != 0:
            return before + l[end]
        else:
            return before


@Pure
def odd_sum(l: List[int]) -> int:
    Requires(Acc(list_pred(l), 1 / 2))
    return odd_sum_rec(l, len(l) - 1)


def m(l: List[int]) -> int:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    Ensures(Result() == odd_sum(l))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    result = 0
    index = -1
    while index < len(l) - 1:
        Invariant(Acc(list_pred(l), 3/4))
        Invariant(index >= -1 and index <= len(l) - 1)
        Invariant(result == odd_sum_rec(l, index))
        old_index = index
        old_result = result
        index += 1
        if l[index] % 2 == 0:
            Assert(result == odd_sum_rec(l, index - 1))
            continue
        result += l[index]
        Assert(index != -1)
        Assert(result == odd_sum_rec(l, index - 1) + l[index])
    return result