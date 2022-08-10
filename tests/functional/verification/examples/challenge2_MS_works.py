from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class SR:
    def __init__(self, runs: List[int], data: List[int]) -> None:
        Requires(MustTerminate(1))
        self.runs = runs
        self.data = data
        Ensures(Acc(self.runs) and Acc(self.data) and self.runs is runs and self.data is data)


def merge(r1: SR, r2: SR) -> SR:
    Requires(Acc(r1.runs, 1/2) and Acc(r1.data, 1/2) and Acc(list_pred(r1.runs), 1/2) and Acc(list_pred(r1.data), 1/2))
    Requires(Acc(r2.runs, 1/2) and Acc(r2.data, 1/2) and Acc(list_pred(r2.runs), 1/2) and Acc(list_pred(r2.data), 1/2))
    Requires(len(r1.runs) > 0 and len(r2.runs) > 0 and len(r1.data) > 0 and len(r2.data) > 0)
    Requires(r1.runs[-1] == len(r1.data))
    Requires(r2.runs[-1] == len(r2.data))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1, 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1]
                                            and r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(r2.runs) - 1, 0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1]
                                            and r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))
    Requires(MustTerminate(4))
    Ensures(Acc(Result().runs) and Acc(Result().data) and list_pred(Result().runs) and list_pred(Result().data))
    Ensures(len(Result().data) == Old(len(r1.data)) + Old(len(r2.data)))
    Ensures(len(Result().runs) > 0 and Result().runs[-1] == len(Result().data))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(Result().runs) - 1,
                                           0 < Result().runs[i] and Result().runs[i] < Result().runs[i + 1] and
                                           Result().runs[i] < len(Result().data)), [[Result().runs[i]]])))

    data = []  # type: List[int]
    runs = []  # type: List[int]
    res = SR(runs, data)

    outer_loop(r1, r2, res)

    return res

def outer_loop(r1: SR, r2: SR, res: SR) -> None:
    Requires(Acc(res.data, 1 / 4))
    Requires(list_pred(res.data) and len(res.data) == 0)
    Requires(Acc(res.runs, 1 / 4))
    Requires(list_pred(res.runs) and len(res.runs) == 0)
    Requires(Acc(r1.runs, 1 / 4) and Acc(list_pred(r1.runs), 1 / 4))
    Requires(Acc(r2.runs, 1 / 4) and Acc(list_pred(r2.runs), 1 / 4))
    Requires(Acc(r1.data, 1 / 4) and Acc(list_pred(r1.data), 1 / 4))
    Requires(Acc(r2.data, 1 / 4) and Acc(list_pred(r2.data), 1 / 4))
    Requires(len(r1.runs) > 0 and len(r2.runs) > 0 and len(r1.data) > 0 and len(r2.data) > 0)
    Requires(r1.runs[-1] == len(r1.data))
    Requires(r2.runs[-1] == len(r2.data))
    Requires(
        Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1, 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1]
                                       and r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
    Requires(
        Forall(int, lambda i: (Implies(i >= 0 and i < len(r2.runs) - 1, 0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1]
                                       and r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))

    Requires(MustTerminate(3))

    Ensures(Acc(res.data, 1 / 4))
    Ensures(list_pred(res.data))
    Ensures(Acc(res.runs, 1 / 4))
    Ensures(list_pred(res.runs))
    Ensures(Acc(r1.runs, 1 / 4) and Acc(list_pred(r1.runs), 1 / 4))
    Ensures(Acc(r2.runs, 1 / 4) and Acc(list_pred(r2.runs), 1 / 4))
    Ensures(Acc(r1.data, 1 / 4) and Acc(list_pred(r1.data), 1 / 4))
    Ensures(Acc(r2.data, 1 / 4) and Acc(list_pred(r2.data), 1 / 4))
    Ensures(len(r1.runs) > 0 and len(r2.runs) > 0 and len(r1.data) > 0 and len(r2.data) > 0)
    Ensures(r1.runs[-1] == len(r1.data))
    Ensures(r2.runs[-1] == len(r2.data))
    Ensures(
        Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1, 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1]
                                       and r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
    Ensures(
        Forall(int, lambda i: (Implies(i >= 0 and i < len(r2.runs) - 1, 0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1]
                                       and r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))
    Ensures(len(res.data) == Old(len(r1.data)) + Old(len(r2.data)))
    Ensures(len(res.runs) > 0 and res.runs[-1] == len(res.data))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(res.runs) - 1,
                                           0 < res.runs[i] and res.runs[i] < res.runs[i + 1] and
                                           res.runs[i] < len(res.data)), [[res.runs[i]]])))

    di1 = 0
    di2 = 0
    ri1 = 0
    ri2 = 0

    while ri1 < len(r1.runs) or ri2 < len(r2.runs):
        Invariant(Acc(res.data, 1 / 6))
        Invariant(list_pred(res.data))
        Invariant(Acc(res.runs, 1 / 6))
        Invariant(list_pred(res.runs))
        Invariant(Acc(r1.runs, 1 / 6) and Acc(list_pred(r1.runs), 1 / 6))
        Invariant(Acc(r2.runs, 1 / 6) and Acc(list_pred(r2.runs), 1 / 6))
        Invariant(Acc(r1.data, 1 / 6) and Acc(list_pred(r1.data), 1 / 6))
        Invariant(Acc(r2.data, 1 / 6) and Acc(list_pred(r2.data), 1 / 6))
        Invariant(len(r1.runs) > 0 and len(r2.runs) > 0 and len(r1.data) > 0 and len(r2.data) > 0)
        Invariant(ri1 >= 0 and ri2 >= 0)
        Invariant(ri1 <= len(r1.runs) and ri2 <= len(r2.runs))
        Invariant(di1 >= 0 and di2 >= 0)
        Invariant(di1 <= len(r1.data) and di2 <= len(r2.data))
        Invariant(r1.runs[-1] == len(r1.data))
        Invariant(r2.runs[-1] == len(r2.data))
        Invariant(Forall(int, lambda i: (
        Implies(i >= 0 and i < len(r1.runs) - 1, 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1]
                and r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
        Invariant(Forall(int, lambda i: (
        Implies(i >= 0 and i < len(r2.runs) - 1, 0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1]
                and r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))
        Invariant(Implies(ri1 == 0, di1 == 0))
        Invariant(Implies(ri1 > 0, di1 == r1.runs[ri1 - 1]))
        Invariant(Implies(ri2 == 0, di2 == 0))
        Invariant(Implies(ri2 > 0, di2 == r2.runs[ri2 - 1]))
        Invariant(len(res.data) == di1 + di2)
        Invariant(Implies(ri1 == 0 and ri2 == 0, len(res.runs) == 0))
        Invariant(Implies(ri1 > 0 or ri2 > 0, len(res.runs) > 0 and res.runs[-1] == len(res.data)))
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(res.runs) - 1,
                                                 0 < res.runs[i] and res.runs[i] < res.runs[i + 1] and
                                                 res.runs[i] < len(res.data)), [[res.runs[i]]])))

        Invariant(MustTerminate(len(r1.runs) + len(r2.runs) + 1 - ri1 - ri2))

        if ri1 == 0:
            Assert(di1 == 0)
        Assert(len(r1.data) > 0)
        if ri2 == 0:
            Assert(di2 == 0)
        Assert(len(r2.data) > 0)
        old_run_seq = ToSeq(res.runs)
        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(old_run_seq),
                                              old_run_seq[i] is res.runs[i]
                                              )
                                      , [[old_run_seq[i]]])))
        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(old_run_seq) - 1,
                                              0 < old_run_seq[i] and old_run_seq[i] < old_run_seq[i + 1]),
                                      [[old_run_seq[i]]])))

        t1 = ri1 < len(r1.runs) and (ri2 == len(r2.runs) or r1.data[di1] <= r2.data[di2])
        t2 = ri2 < len(r2.runs) and (ri1 == len(r1.runs) or r2.data[di2] <= r1.data[di1])

        Assert(t1 or t2)

        if t1:
            di1 = inner_loop(r1, res, ri1, di1)
            ri1 += 1

        if t2:
            di2 = inner_loop(r2, res, ri2, di2)
            ri2 += 1

        res.runs.append(len(res.data))

        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(old_run_seq),
                                              old_run_seq[i] is res.runs[i]
                                              )
                                      , [[res.runs[i]]])))


def inner_loop(r1: SR, res: SR, ri1: int, di1: int) -> int:
    Requires(Acc(res.data, 1 / 8))
    Requires(list_pred(res.data))
    Requires(Acc(r1.data, 1 / 8))
    Requires(Acc(list_pred(r1.data), 1 / 8))
    Requires(Acc(r1.runs, 1 / 8))
    Requires(Acc(list_pred(r1.runs), 1 / 8))
    Requires(ri1 >= 0)
    Requires(ri1 < len(r1.runs))
    Requires(di1 >= 0 and di1 <= r1.runs[ri1])
    Requires(r1.runs[-1] == len(r1.data))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1,
                                             0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1] and
                                             r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
    Requires(MustTerminate(2))

    Ensures(Result() == Old(r1.runs[ri1]))
    Ensures(Acc(res.data, 1 / 8))
    Ensures(list_pred(res.data))
    Ensures(Acc(r1.data, 1 / 8))
    Ensures(Acc(list_pred(r1.data), 1 / 8))
    Ensures(Acc(r1.runs, 1 / 8))
    Ensures(Acc(list_pred(r1.runs), 1 / 8))
    Ensures(ri1 >= 0)
    Ensures(ri1 < len(r1.runs))
    Ensures(di1 >= 0 and di1 <= r1.runs[ri1])
    Ensures(r1.runs[-1] == len(r1.data))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1,
                                             0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1] and
                                             r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
    Ensures(len(res.data) == Old(len(res.data)) + (Result() - di1))

    old_di1 = di1
    while di1 < r1.runs[ri1]:
        Invariant(Acc(res.data, 1 / 8))
        Invariant(list_pred(res.data))
        Invariant(Acc(r1.data, 1 / 16))
        Invariant(Acc(list_pred(r1.data), 1 / 16))
        Invariant(Acc(r1.runs, 1 / 16))
        Invariant(Acc(list_pred(r1.runs), 1 / 16))
        Invariant(ri1 >= 0)
        Invariant(ri1 < len(r1.runs))
        Invariant(di1 >= 0 and di1 <= r1.runs[ri1])
        Invariant(r1.runs[-1] == len(r1.data))
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1,
                                                 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1] and
                                                 r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
        Invariant(len(res.data) == Old(len(res.data) + (di1 - old_di1)))
        Invariant(MustTerminate(r1.runs[ri1] + 1 - di1))

        Assert(r1.runs[ri1] <= len(r1.data))
        res.data.append(r1.data[di1])
        di1 += 1
    return di1


def msort(a: List[int], l: int, h: int) -> SR:
    Requires(list_pred(a))
    Requires(h >= l)
    Requires(l >= 0 and h <= len(a))
    Requires(MustTerminate(h - l + 5))
    Ensures(Acc(list_pred(a)))
    Ensures(ToSeq(a) is Old(ToSeq(a)))
    Ensures(Acc(Result().runs) and Acc(Result().data) and list_pred(Result().runs) and list_pred(Result().data))
    Ensures(Implies(h > l, len(Result().runs) > 0))
    Ensures(len(Result().data) == h - l)
    Ensures(Implies(h > l, Result().runs[-1] == len(Result().data)))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(Result().runs) - 1,
                                           0 < Result().runs[i] and Result().runs[i] < Result().runs[i + 1] and
                                           Result().runs[i] < len(Result().data)), [[Result().runs[i]]])))
    #Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(Result().data) - 1,
    #                                       0 < Result().data[i] and Result().data[i] < Result().data[i + 1]), [[Result().data[i]]])))

    data = []  # type: List[int]
    runs = []  # type: List[int]
    res = SR(runs, data)
    if l == h:
        return res
    if h - l == 1:
        res.data.append(a[l])
        res.runs.append(len(res.data))
        return res
    m = l + (h - l) // 2
    res1 = msort(a, l, m)
    res2 = msort(a, m, h)
    res = merge(res1, res2)

    return res
