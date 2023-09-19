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
    Ensures(Old(ToMS(ToSeq(arr))) == ToMS(ToSeq(Result())))
    Ensures(Forall(int, lambda i: (Implies(i in Result(), Old(i in arr)), [[i in Result()]])))
    Ensures(Forall2(int, int, lambda i, j: (Implies(i >= 0 and i < j and j < len(Result()), Result()[i] <= Result()[j]), [[Result()[i], Result()[j]]])))
    less = []  # type: List[int]
    pivotList = []  # type: List[int]
    more = []  # type: List[int]
    if len(arr) <= 1:
        return arr
    else:
        pivot = arr[0]
        j = 0
        while j < len(arr):
            Invariant(list_pred(less) and list_pred(pivotList) and list_pred(more))
            Invariant(Implies(j > 0, len(pivotList) > 0))
            Invariant(Acc(list_pred(arr), 1/2) and len(arr) > 0 and arr[0] == pivot)
            Invariant(j >= 0 and j <= len(arr))
            Invariant(pivot in arr)
            Invariant(ToMS(ToSeq(less)) + ToMS(ToSeq(more)) + ToMS(ToSeq(pivotList)) == ToMS(ToSeq(arr).take(j)))
            Invariant(Forall(int, lambda k: (Implies(k >= 0 and k < len(pivotList), pivotList[k] == pivot and pivot in arr), [[pivotList[k]]])))
            Invariant(Forall(int, lambda k: (Implies(k >= 0 and k < len(less), less[k] < pivot), [[less[k]]])))
            Invariant(Forall(int, lambda k: (Implies(k in less, k in arr and k < pivot), [[k in less]])))
            Invariant(Forall(int, lambda k: (Implies(k >= 0 and k < len(more), more[k] > pivot), [[more[k]]])))
            Invariant(Forall(int, lambda k: (Implies(k in more, k in arr and k > pivot), [[k in more]])))
            Invariant(Forall(int, lambda k: (Implies(k in pivotList, k in arr), [[k in pivotList]])))
            Invariant(MustTerminate(len(arr) - j))

            i = arr[j]

            if i < pivot:
                less.append(i)
            elif i > pivot:
                more.append(i)
            else:
                pivotList.append(i)
            tmp = ToSeq(arr).take(j) + PSeq(i)
            Assert(tmp == ToSeq(arr).take(j + 1))
            j += 1

        Assert(ToSeq(arr).take(j) == ToSeq(arr))
        less = quickSort(less)
        more = quickSort(more)
        Assert(Forall(int, lambda i: (Implies(i in less, Old(i in arr)), [[i in less]])))
        Assert(Forall(int, lambda i: (Implies(i in more, Old(i in arr)), [[i in more]])))
        Assert(Forall(int, lambda i: (Implies(i in pivotList, Old(i in arr)), [[i in pivotList]])))
        res = less + pivotList + more
        Assert(Forall2(int, int, lambda i, j: (Implies(0 <= i and 0 <= j and i < len(less) and j < len(pivotList), less[i] in less and less[i] < pivotList[j]), [[less[i], pivotList[j]]])))
        Assert(Forall2(int, int, lambda i, j: (Implies(0 <= i and 0 <= j and i < len(more) and j < len(pivotList), more[i] in more and more[i] > pivotList[j]),[[more[i], pivotList[j]]])))
        Assert(Forall2(int, int, lambda i, j: (Implies(0 <= i and 0 <= j and i < len(less) and j < len(more), less[i] in less and more[j] in more and less[i] < more[j]),[[less[i], more[j]]])))
        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(res), res[i] is (less[i] if i < len(less) else (pivotList[i - len(less)] if i < len(less) + len(pivotList) else more[i - len(less) - len(pivotList)]))), [[res[i]]])))
        Assert(ToMS(ToSeq(res)) == ToMS(ToSeq(less)) + ToMS(ToSeq(pivotList)) + ToMS(ToSeq(more)))
        return res
