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
    Requires(Acc(r1.runs, 1 / 2) and Acc(r1.data, 1 / 2) and Acc(list_pred(r1.runs), 1 / 2) and Acc(list_pred(r1.data), 1 / 2))
    Requires(Acc(r2.runs, 1 / 2) and Acc(r2.data, 1 / 2) and Acc(list_pred(r2.runs), 1 / 2) and Acc(list_pred(r2.data), 1 / 2))
    Requires(len(r1.runs) > 0 and len(r2.runs) > 0 and len(r1.data) > 0 and len(r2.data) > 0)
    Requires(r1.runs[-1] == len(r1.data))
    Requires(r2.runs[-1] == len(r2.data))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1, 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1]
                                            and r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
    Requires(Forall(int, lambda i: (Implies(i >= 0 and i < len(r2.runs) - 1, 0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1]
                                            and r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))
    Requires(MustTerminate(2))
    Ensures(Acc(Result().runs) and Acc(Result().data) and list_pred(Result().runs) and list_pred(Result().data))
    # new
    #Ensures(len(Result().runs) > 0)
    #Ensures(len(Result().data) == Old(len(r1.data)) + Old(len(r2.data)))
    #Ensures(Result().runs[-1] == len(Result().data))
    #Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(Result().runs) - 1,
    #                                      0 < Result().runs[i] and Result().runs[i] < Result().runs[i + 1] and
    #                                      Result().runs[i] < len(Result().data)), [[Result().runs[i]]])))

    data = []  # type: List[int]
    runs = []  # type: List[int]
    res = SR(runs, data)
    di1 = 0
    di2 = 0
    ri1 = 0
    ri2 = 0

    while ri1 < len(r1.runs) or ri2 < len(r2.runs):
        #Invariant(Acc(res.data, 1 / 4))
        Invariant(list_pred(data))
        #Invariant(Acc(res.runs, 1 / 4))
        Invariant(list_pred(runs))
        Invariant(Acc(r1.runs, 1 / 4) and Acc(list_pred(r1.runs), 1 / 4))
        Invariant(Acc(r2.runs, 1 / 4) and Acc(list_pred(r2.runs), 1 / 4))
        Invariant(Acc(r1.data, 1 / 4) and Acc(list_pred(r1.data), 1 / 4))
        Invariant(Acc(r2.data, 1 / 4) and Acc(list_pred(r2.data), 1 / 4))
        Invariant(len(r1.runs) > 0 and len(r2.runs) > 0 and len(r1.data) > 0 and len(r2.data) > 0)
        Invariant(ri1 >= 0 and ri2 >= 0)
        Invariant(ri1 <= len(r1.runs) and ri2 <= len(r2.runs))
        Invariant(di1 >= 0 and di2 >= 0)
        Invariant(di1 <= len(r1.data) and di2 <= len(r2.data))
        Invariant(r1.runs[-1] == len(r1.data))
        Invariant(r2.runs[-1] == len(r2.data))
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1, 0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1]
                                                 and r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(r2.runs) - 1, 0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1]
                                                 and r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))
        Invariant(Implies(ri1 == 0, di1 == 0))
        Invariant(Implies(ri1 > 0, di1 == r1.runs[ri1-1]))
        Invariant(Implies(ri2 == 0, di2 == 0))
        Invariant(Implies(ri2 > 0, di2 == r2.runs[ri2-1]))
        # new
        #Invariant(Implies(ri1 > 0 or ri2 > 0, len(runs) > 0 and runs[-1] == len(data)))

        Invariant(MustTerminate(len(r1.runs) + len(r2.runs) + 1 - ri1 - ri2))

        if ri1 == 0:
            Assert(di1 == 0)
        Assert(len(r1.data) > 0)
        if ri2 == 0:
            Assert(di2 == 0)
        Assert(len(r2.data) > 0)
        t1 = ri1 < len(r1.runs) and (ri2 == len(r2.runs) or r1.data[di1] <= r2.data[di2])
        t2 = ri2 < len(r2.runs) and (ri1 == len(r1.runs) or r2.data[di2] <= r1.data[di1])

        if t1:
            while di1 < r1.runs[ri1]:
                # Invariant(Acc(res.data, 1/4))
                Invariant(list_pred(data))
                Invariant(Acc(r1.data, 1 / 4))
                Invariant(Acc(list_pred(r1.data), 1 / 4))
                Invariant(Acc(r1.runs, 1/4))
                Invariant(Acc(list_pred(r1.runs), 1/4))
                Invariant(ri1 >= 0)
                Invariant(ri1 < len(r1.runs))
                Invariant(di1 >= 0 and di1 <= r1.runs[ri1])
                Invariant(r1.runs[-1] == len(r1.data))
                Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(r1.runs) - 1,
                                                         0 < r1.runs[i] and r1.runs[i] < r1.runs[i + 1] and
                                                         r1.runs[i] < len(r1.data)), [[r1.runs[i]]])))
                Invariant(MustTerminate(r1.runs[ri1] + 1 - di1))

                Assert(r1.runs[ri1] <= len(r1.data))
                data.append(r1.data[di1])
                di1 += 1
            ri1 += 1

        if t2:
            while di2 < r2.runs[ri2]:
                #Invariant(Acc(res.data, 1 / 4))
                Invariant(list_pred(data))
                Invariant(Acc(r2.data, 1 / 4))
                Invariant(Acc(list_pred(r2.data), 1 / 4))
                Invariant(Acc(r2.runs, 1 / 4))
                Invariant(Acc(list_pred(r2.runs), 1 / 4))
                Invariant(ri2 >= 0)
                Invariant(ri2 < len(r2.runs))
                Invariant(di2 >= 0 and di2 <= r2.runs[ri2])
                Invariant(r2.runs[-1] == len(r2.data))
                Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(r2.runs) - 1,
                                                         0 < r2.runs[i] and r2.runs[i] < r2.runs[i + 1] and
                                                         r2.runs[i] < len(r2.data)), [[r2.runs[i]]])))
                Invariant(MustTerminate(r2.runs[ri2] + 1 - di2))

                data.append(r2.data[di2])
                di2 += 1
            ri2 += 1

        runs.append(len(data))

    return res


def msort(a: List[int], l: int, h: int) -> SR:
    Requires(list_pred(a))
    Requires(h >= l)
    Requires(l >= 0 and h <= len(a))
    Requires(MustTerminate(h - l + 4))
    Ensures(Acc(list_pred(a)))
    Ensures(ToSeq(a) is Old(ToSeq(a)))
    Ensures(Acc(Result().runs) and Acc(Result().data) and list_pred(Result().runs) and list_pred(Result().data))
    Ensures(Implies(h > l, len(Result().runs) > 0))
    Ensures(len(Result().data) == h - l)
    Ensures(Implies(h > l, Result().runs[-1] == len(Result().data)))
    Ensures(Forall(int, lambda i: (Implies(i >= 0 and i < len(Result().runs) - 1,
                                           0 < Result().runs[i] and Result().runs[i] < Result().runs[i + 1] and
                                           Result().runs[i] < len(Result().data)), [[Result().runs[i]]])))

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

    # assume correct functional behavior of merge.

    return res
