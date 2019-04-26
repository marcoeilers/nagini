# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import List, cast
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


def quickSort(arr: List[int]) -> List[int]:
    Requires(Acc(list_pred(arr), 2/3))
    Requires(MustTerminate(2 + len(arr)))
    Ensures(Acc(list_pred(arr), 2/3))
    Ensures(Implies(len(arr) > 1, list_pred(Result())))
    Ensures(Implies(len(arr) <= 1, Result() is arr))
    less = []  # type: List[int]
    pivotList = []  # type: List[int]
    more = []  # type: List[int]
    if len(arr) <= 1:
        return arr
    else:
        pivot = arr[0]
        for i in arr:
            Invariant(list_pred(less) and list_pred(pivotList) and list_pred(more))
            Invariant(len(Previous(i)) == len(less) + len(more) + len(pivotList))
            Invariant(Implies(len(Previous(i)) > 0, len(pivotList) > 0))
            Invariant(Acc(list_pred(arr), 1/2) and len(arr) > 0 and arr[0] == pivot)
            Invariant(MustTerminate(len(arr) - len(Previous(i))))
            if i < pivot:
                less.append(i)
            elif i > pivot:
                more.append(i)
            else:
                pivotList.append(i)
        less = quickSort(less)
        more = quickSort(more)
        return less + pivotList + more