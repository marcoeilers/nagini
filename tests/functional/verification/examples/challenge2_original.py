from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class SR:
    def __init__(self, runs: List[int], data: List[int]) -> None:
        Requires(MustTerminate(1))
        self.runs = runs
        self.data = data
        Ensures(Acc(self.runs) and Acc(self.data) and self.runs is runs and self.data is data)


class Runtime:
    def __init__(self) -> None:
        self.steps = 0
        Ensures(Acc(self.steps) and self.steps == 0)


RT = Runtime()

@Pure
def triggera1(i: int) -> bool:
    return True

@Pure
def triggerb1(j: int) -> bool:
    return True

@Pure
def triggerc1(i: int) -> bool:
    return True

@Pure
def triggerd1(i: int) -> bool:
    return True


@Pure
def runs_bounds(runs: PSeq[int], data: PSeq[int], end: int) -> bool:
    return (
        (len(runs) > 0 and len(data) > 0) and
        (runs[-1] == end) and
        (Forall(int, lambda i: (Implies(i >= 0 and i < len(runs) - 1, 0 < runs[i] and runs[i] < runs[i + 1]
                                        and runs[i] < len(data)), [[runs[i]]])))
    )


@Pure
def correct_runs(runs: PSeq[int], data: PSeq[int], end: int) -> bool:
    Requires(0 <= end and end <= len(data))
    Requires(runs_bounds(runs, data, end))
    return ((Implies(len(runs) > 1, data[0] < data[runs[0]])) and
            (Forall(int, lambda j: (Implies(j > 0 and j < runs[0] and triggerc1(j),
                                            data[j] == data[0]), [[triggerc1(j)]]))) and
            (Forall(int, lambda i: (Implies(i >= 0 and i < len(runs) - 1 and triggera1(i),
                                            Forall(int, lambda j: (Implies(j > runs[i] and j < runs[i + 1] and triggerb1(j),
                                                                           data[j] == data[runs[i]]),
                                                                   [[triggerb1(j)]]))),
                                    [[triggera1(i)]]))) and
            (Forall(int, lambda i: (Implies(i >= 0 and i < len(runs) - 2 and triggerd1(i),
                                            data[runs[i]] < data[runs[i + 1]]),
                                    [[triggerd1(i)]])))
            )


PROVE_CORRECT_RUNS = False


PROVE_PERMUTATION = True


PROVE_RUNTIME = False


def sorted_proof(runs: PSeq[int], data: PSeq[int], j: int) -> None:
    Requires(runs_bounds(runs, data, len(data)))
    Requires(correct_runs(runs, data, len(data)))
    Requires(j >= 0 and j < len(data) - 1)
    Ensures(data[j] <= data[j+1])
    if runs[0] > j:
        i = 0
        Assert(triggerc1(j))
    else:
        i = 1
        while i < len(runs) and runs[i] <= j:
            Invariant(i >= 1 and i <= len(runs))
            Invariant(runs[i - 1] <= j)
            Invariant(MustTerminate(len(runs) - i))

            i += 1
        Assert(triggera1(i - 1))
        Assert(triggerb1(j))
    if runs[i] > j + 1:
        if i == 0:
            Assert(triggerc1(j + 1))
        else:
            Assert(triggerb1(j + 1))
    else:
        Assert(triggerd1(i - 1))


def merge(r1: SR, r2: SR) -> SR:
    Requires(Acc(r1.runs, 1/2) and Acc(r1.data, 1/2) and Acc(list_pred(r1.runs), 1/2) and Acc(list_pred(r1.data), 1/2))
    Requires(Acc(r2.runs, 1/2) and Acc(r2.data, 1/2) and Acc(list_pred(r2.runs), 1/2) and Acc(list_pred(r2.data), 1/2))
    Requires(runs_bounds(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
             runs_bounds(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data))))
    Requires(Implies(PROVE_CORRECT_RUNS,
                     correct_runs(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
                     correct_runs(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data)))))
    Requires(Implies(PROVE_RUNTIME, Acc(RT.steps)))
    Requires(MustTerminate(4))
    Ensures(Acc(Result().runs) and Acc(Result().data) and list_pred(Result().runs) and list_pred(Result().data))
    Ensures(len(ToSeq(Result().data)) == Old(len(ToSeq(r1.data))) + Old(len(ToSeq(r2.data))))
    Ensures(runs_bounds(ToSeq(Result().runs), ToSeq(Result().data), len(ToSeq(Result().data))))
    Ensures(Implies(PROVE_CORRECT_RUNS, correct_runs(ToSeq(Result().runs), ToSeq(Result().data), len(ToSeq(Result().data)))))
    Ensures(Implies(PROVE_PERMUTATION, ToMS(ToSeq(Result().data)) is Old(ToMS(ToSeq(r1.data))) + Old(ToMS(ToSeq(r2.data)))))
    Ensures(Implies(PROVE_RUNTIME, Acc(RT.steps) and RT.steps == Old(RT.steps) + Old(len(r1.data)) + Old(len(r2.data))))

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
    Requires(runs_bounds(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
             runs_bounds(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data))))
    Requires(Implies(PROVE_CORRECT_RUNS, correct_runs(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
                                         correct_runs(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data)))))
    Requires(MustTerminate(3))

    Ensures(Acc(res.data, 1 / 4))
    Ensures(list_pred(res.data))
    Ensures(Acc(res.runs, 1 / 4))
    Ensures(list_pred(res.runs))
    Ensures(Acc(r1.runs, 1 / 4) and Acc(list_pred(r1.runs), 1 / 4))
    Ensures(Acc(r2.runs, 1 / 4) and Acc(list_pred(r2.runs), 1 / 4))
    Ensures(Acc(r1.data, 1 / 4) and Acc(list_pred(r1.data), 1 / 4))
    Ensures(Acc(r2.data, 1 / 4) and Acc(list_pred(r2.data), 1 / 4))
    Ensures(runs_bounds(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
            runs_bounds(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data))))
    Ensures(len(ToSeq(res.data)) == Old(len(ToSeq(r1.data))) + Old(len(ToSeq(r2.data))))
    Ensures(runs_bounds(ToSeq(res.runs), ToSeq(res.data), len(ToSeq(res.data))))
    Ensures(Implies(PROVE_CORRECT_RUNS, correct_runs(ToSeq(res.runs), ToSeq(res.data), len(ToSeq(res.data)))))
    Ensures(Implies(PROVE_PERMUTATION, ToMS(ToSeq(res.data)) == ToMS(ToSeq(r1.data)) + ToMS(ToSeq(r2.data))))

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
        Invariant(runs_bounds(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
                  runs_bounds(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data))))
        Invariant(Implies(PROVE_CORRECT_RUNS, correct_runs(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))) and
                                              correct_runs(ToSeq(r2.runs), ToSeq(r2.data), len(ToSeq(r2.data)))))
        Invariant(Implies(ri1 == 0 and ri2 == 0, len(res.data) == 0 and len(res.runs) == 0))
        Invariant(Implies(ri1 > 0 or ri2 > 0, len(ToSeq(res.data)) > 0 and len(ToSeq(res.runs)) > 0 and
                          runs_bounds(ToSeq(res.runs), ToSeq(res.data), len(ToSeq(res.data)))))
        Invariant(Implies(PROVE_CORRECT_RUNS and (ri1 > 0 or ri2 > 0), correct_runs(ToSeq(res.runs), ToSeq(res.data), len(ToSeq(res.data)))))
        Invariant(ri1 >= 0 and ri2 >= 0)
        Invariant(ri1 <= len(ToSeq(r1.runs)) and ri2 <= len(ToSeq(r2.runs)))
        Invariant(di1 >= 0 and di2 >= 0)
        Invariant(di1 <= len(ToSeq(r1.data)) and di2 <= len(ToSeq(r2.data)))
        Invariant(Implies(ri1 == 0, di1 == 0))
        Invariant(Implies(ri1 > 0, di1 == ToSeq(r1.runs)[ri1 - 1]))
        Invariant(Implies(ri2 == 0, di2 == 0))
        Invariant(Implies(ri2 > 0, di2 == ToSeq(r2.runs)[ri2 - 1]))
        Invariant(len(ToSeq(res.data)) == di1 + di2)
        Invariant(Implies(ri1 == 0 and ri2 == 0, len(ToSeq(res.runs)) == 0))
        Invariant(Implies(ri1 > 0 or ri2 > 0, len(ToSeq(res.runs)) > 0 and ToSeq(res.runs)[-1] == len(ToSeq(res.data))))
        Invariant(Forall(int, lambda i: (Implies(i >= 0 and i < len(ToSeq(res.runs)) - 1,
                                                 0 < ToSeq(res.runs)[i] and ToSeq(res.runs)[i] < ToSeq(res.runs)[i + 1] and
                                                 ToSeq(res.runs)[i] < len(ToSeq(res.data))), [[ToSeq(res.runs)[i]]])))
        Invariant(Implies(PROVE_CORRECT_RUNS and len(ToSeq(res.data)) > 0 and di1 < len(ToSeq(r1.data)), res.data[-1] < r1.data[di1]))
        Invariant(Implies(PROVE_CORRECT_RUNS and len(ToSeq(res.data)) > 0 and di2 < len(ToSeq(r2.data)), res.data[-1] < r2.data[di2]))
        Invariant(Implies(PROVE_PERMUTATION, ToMS(ToSeq(res.data)) == ToMS(ToSeq(r1.data).take(di1)) + ToMS(ToSeq(r2.data).take(di2))))

        Invariant(MustTerminate(len(r1.runs) + len(r2.runs) + 1 - ri1 - ri2))

        if ri1 == 0:
            Assert(di1 == 0)
        Assert(len(r1.data) > 0)
        if ri2 == 0:
            Assert(di2 == 0)
        Assert(len(r2.data) > 0)
        old_run_seq = ToSeq(res.runs)
        old_data_seq = ToSeq(res.data)
        old_di1 = di1
        old_di2 = di2
        old_r1_data = ToSeq(r1.data).take(di1)
        old_r2_data = ToSeq(r2.data).take(di2)

        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(old_run_seq),
                                              old_run_seq[i] is ToSeq(res.runs)[i]
                                              )
                                      , [[old_run_seq[i]]])))
        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(old_run_seq) - 1,
                                              0 < old_run_seq[i] and old_run_seq[i] < old_run_seq[i + 1]),
                                      [[old_run_seq[i]]])))

        t1 = ri1 < len(r1.runs) and (ri2 == len(r2.runs) or r1.data[di1] <= r2.data[di2])
        t2 = ri2 < len(r2.runs) and (ri1 == len(r1.runs) or r2.data[di2] <= r1.data[di1])

        Assert(t1 or t2)

        end = len(res.data)
        Assume(SplitOn(t1, SplitOn(t2)))
        Assert(Implies(PROVE_CORRECT_RUNS and len(ToSeq(res.runs)) > 1, ToSeq(res.data)[0] < ToSeq(res.data)[ToSeq(res.runs)[0]]))

        if t1:
            to_add_d1 = ToSeq(r1.data)[di1]

            di1 = inner_loop(r1, res, ri1, di1, end)
            ri1 += 1

            if PROVE_CORRECT_RUNS:
                Assert(ToSeq(res.data)[len(res.data)-1] == to_add_d1)
                Assume(SplitOn(len(ToSeq(res.runs)) == 1))

                if len(ToSeq(res.runs)) == 1:
                    Assert(triggerd1(ri1 - 2))  # needed
                    Assert(triggerc1(len(old_data_seq) - 1))  # needed

                else:
                    runs = ToSeq(res.runs)
                    data = ToSeq(res.data)
                    cur_i = len(runs) - 2
                    Assert(triggera1(cur_i))
                    Assert(triggerb1(len(old_data_seq) - 1))

        if t2:
            to_add_d2 = ToSeq(r2.data)[di2]
            if PROVE_CORRECT_RUNS and t1:
                Assert(to_add_d1 == to_add_d2)
            di2 = inner_loop(r2, res, ri2, di2, end)
            ri2 += 1

            if PROVE_CORRECT_RUNS:
                Assert(ToSeq(res.data)[len(res.data) - 1] == to_add_d2)
                Assume(SplitOn(len(ToSeq(res.runs)) == 1))

                if len(ToSeq(res.runs)) == 1:
                    Assert(triggerd1(ri2 - 2))  # needed
                    Assert(triggerc1(len(old_data_seq) - 1))  # needed

                else:
                    runs = ToSeq(res.runs)
                    data = ToSeq(res.data)
                    cur_i = len(runs) - 2
                    Assert(triggera1(cur_i))
                    Assert(triggerb1(len(old_data_seq) - 1))

        Assert(Implies(PROVE_PERMUTATION,
                       ToSeq(res.data) == old_data_seq + ToSeq(r1.data).drop(old_di1).take(di1 - old_di1) +
                       ToSeq(r2.data).drop(old_di2).take(di2 - old_di2)))
        Assert(Implies(PROVE_PERMUTATION,
                       ToSeq(r1.data).take(di1) == old_r1_data + ToSeq(r1.data).drop(old_di1).take(di1 - old_di1)))
        Assert(Implies(PROVE_PERMUTATION,
                       ToSeq(r2.data).take(di2) == old_r2_data + ToSeq(r2.data).drop(old_di2).take(di2 - old_di2)))

        Assert(old_run_seq is ToSeq(res.runs))
        res.runs.append(len(res.data))

        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(old_run_seq),
                                              old_run_seq[i] is ToSeq(res.runs)[i]
                                              )
                                      , [[ToSeq(res.runs)[i]]])))
        # Assert(runs_bounds(ToSeq(res.runs), ToSeq(res.data), len(ToSeq(res.data))))

    Assert(Implies(PROVE_PERMUTATION,
                   ToSeq(r1.data).take(di1) == ToSeq(r1.data)))
    Assert(Implies(PROVE_PERMUTATION,
                   ToSeq(r2.data).take(di2) == ToSeq(r2.data)))


def inner_loop(r1: SR, res: SR, ri1: int, di1: int, end: int) -> int:
    Requires(Acc(res.data, 1 / 8))
    Requires(list_pred(res.data))
    Requires(Acc(res.runs, 1 / 8))
    Requires(Acc(list_pred(res.runs), 1 / 8))
    Requires(Acc(r1.data, 1 / 8))
    Requires(Acc(list_pred(r1.data), 1 / 8))
    Requires(Acc(r1.runs, 1 / 8))
    Requires(Acc(list_pred(r1.runs), 1 / 8))
    Requires(ri1 >= 0)
    Requires(ri1 < len(ToSeq(r1.runs)))
    Requires(di1 >= 0 and di1 <= ToSeq(r1.runs)[ri1])
    Requires(runs_bounds(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data))))
    Requires(Implies(PROVE_CORRECT_RUNS, correct_runs(ToSeq(r1.runs), ToSeq(r1.data), len(ToSeq(r1.data)))))
    Requires((ri1 == 0 and di1 == 0) or (ri1 > 0 and di1 == ToSeq(r1.runs)[ri1 - 1]))
    Requires(end >= 0 and end <= len(ToSeq(res.data)))
    Requires(Implies(len(res.runs) > 0, runs_bounds(ToSeq(res.runs), ToSeq(res.data), end)))
    Requires(Implies(PROVE_CORRECT_RUNS and len(res.runs) > 0, correct_runs(ToSeq(res.runs), ToSeq(res.data), end)))

    Requires(MustTerminate(2))

    Ensures(Result() == Old(r1.runs[ri1]))
    Ensures(Acc(res.data, 1 / 8))
    Ensures(list_pred(res.data))
    Ensures(Acc(res.runs, 1 / 8))
    Ensures(Acc(list_pred(res.runs), 1 / 8) and ToSeq(res.runs) is Old(ToSeq(res.runs)))
    Ensures(Acc(r1.data, 1 / 8))
    Ensures(Acc(list_pred(r1.data), 1 / 8))
    Ensures(Acc(r1.runs, 1 / 8))
    Ensures(Acc(list_pred(r1.runs), 1 / 8))
    Ensures(len(ToSeq(res.data)) == Old(len(ToSeq(res.data))) + (Result() - di1))
    Ensures(ToSeq(r1.runs) is Old(ToSeq(r1.runs)))
    Ensures((ri1 == 0 and di1 == 0) or (ri1 > 0 and di1 == ToSeq(r1.runs)[ri1 - 1]))
    Ensures(end >= 0 and end <= len(ToSeq(res.data)))
    Ensures(Implies(len(res.runs) > 0, runs_bounds(ToSeq(res.runs), ToSeq(res.data), end)))
    Ensures(Implies(PROVE_CORRECT_RUNS and len(res.runs) > 0, correct_runs(ToSeq(res.runs), ToSeq(res.data), end)))
    Ensures(Implies(PROVE_CORRECT_RUNS,
                    Forall(int, lambda i: (Implies(i >= 0 and i < Old(len(ToSeq(res.data))), ToSeq(res.data)[i] is Old(ToSeq(res.data))[i]), [[ToSeq(res.data)[i]]]))))
    Ensures(Implies(PROVE_CORRECT_RUNS,
                    Forall(int, lambda i: (Implies(i >= Old(len(ToSeq(res.data))) and i < len(ToSeq(res.data)), ToSeq(res.data)[i] == Old(ToSeq(r1.data))[di1]), [[ToSeq(res.data)[i]]]))))
    Ensures(Implies(PROVE_CORRECT_RUNS and Result() < len(ToSeq(r1.data)), ToSeq(r1.data)[Result()] > Old(ToSeq(r1.data))[di1]))
    Ensures(Implies(PROVE_PERMUTATION, ToSeq(res.data) == Old(ToSeq(res.data)) + ToSeq(r1.data).drop(di1).take(Result() - di1)))

    Assume(SplitOn(ri1 == 0))
    old_data = ToSeq(res.data)
    old_data_d1 = ToSeq(r1.data)
    old_runs_d1 = ToSeq(r1.runs)
    old_di1 = di1
    old_val = old_data_d1[di1]

    if PROVE_CORRECT_RUNS:
        if ri1 == 0:
            Assert(Forall(int, lambda j: (Implies(j >= old_di1 and j < old_runs_d1[ri1] and triggerc1(j),
                                                  old_data_d1[j] == old_data_d1[di1]), [[old_data_d1[j]]])))
        else:
            Assert(triggera1(ri1 - 1))
            Assert(Forall(int, lambda j: (Implies(j >= old_di1 and j < old_runs_d1[ri1] and triggerb1(j),
                                                  old_data_d1[j] == old_data_d1[di1]), [[old_data_d1[j]]])))


    while di1 < r1.runs[ri1]:
        Invariant(Acc(res.data, 1 / 16))
        Invariant(list_pred(res.data))
        Invariant(Acc(res.runs, 1 / 16))
        Invariant(Acc(list_pred(res.runs), 1 / 16) and ToSeq(res.runs) is Old(ToSeq(res.runs)))
        Invariant(Acc(r1.data, 1 / 16))
        Invariant(Acc(list_pred(r1.data), 1 / 16) and ToSeq(r1.data) is old_data_d1)
        Invariant(Acc(r1.runs, 1 / 16))
        Invariant(Acc(list_pred(r1.runs), 1 / 16) and ToSeq(r1.runs) is old_runs_d1)
        Invariant(ri1 >= 0)
        Invariant(ri1 < len(old_runs_d1))
        Invariant(di1 >= 0 and di1 <= old_runs_d1[ri1] and di1 >= old_di1)
        Invariant(runs_bounds(old_runs_d1, old_data_d1, len(old_data_d1)))
        Invariant(len(ToSeq(res.data)) == Old(len(old_data) + (di1 - old_di1)))
        Invariant(Implies(PROVE_CORRECT_RUNS,
                          Forall(int, lambda i: (Implies(i >= 0 and i < len(old_data), ToSeq(res.data)[i] is old_data[i]), [[ToSeq(res.data)[i]]]))))
        Invariant(Implies(PROVE_CORRECT_RUNS,
                          Forall(int, lambda i: (Implies(i >= len(old_data) and i < len(ToSeq(res.data)), ToSeq(res.data)[i] == old_val), [[ToSeq(res.data)[i]]]))))
        Invariant(Implies(len(res.runs) > 0, runs_bounds(ToSeq(res.runs), ToSeq(res.data), end)))
        Invariant(Implies(PROVE_CORRECT_RUNS and len(res.runs) > 0, correct_runs(ToSeq(res.runs), ToSeq(res.data), end)))
        Invariant(Implies(PROVE_PERMUTATION, ToSeq(res.data) == Old(ToSeq(res.data)) + ToSeq(r1.data).drop(old_di1).take(di1 - old_di1)))

        Invariant(MustTerminate(ToSeq(r1.runs)[ri1] + 1 - di1))

        Assert(ToSeq(r1.runs)[ri1] <= len(ToSeq(r1.data)))
        pre_append_data = ToSeq(res.data)
        Assert(ToSeq(r1.data) is old_data_d1)
        Assert(di1 >= old_di1 and di1 < old_runs_d1[ri1])
        Assert(Implies(PROVE_CORRECT_RUNS, old_data_d1[di1] == old_val))
        res.data.append(r1.data[di1])
        Assert(Forall(int, lambda i: (Implies(i >= 0 and i < len(pre_append_data), ToSeq(res.data)[i] is pre_append_data[i]), [[ToSeq(res.data)[i]]])))

        di1 += 1
    if ri1 > 0:
        Assert(triggerd1(ri1 - 1))
    Assert(Implies(PROVE_CORRECT_RUNS and di1 < len(ToSeq(r1.data)), ToSeq(r1.data)[di1] > Old(ToSeq(r1.data))[old_di1]))
    return di1



def msort(a: List[int], l: int, h: int) -> SR:
    Requires(list_pred(a))
    Requires(h >= l)
    Requires(l >= 0 and h <= len(a))
    Requires(MustTerminate(h - l + 5))
    Requires(Implies(PROVE_RUNTIME, Acc(RT.steps)))
    Ensures(Acc(list_pred(a)))
    Ensures(ToSeq(a) is Old(ToSeq(a)))
    Ensures(Acc(Result().runs) and Acc(Result().data) and list_pred(Result().runs) and list_pred(Result().data))
    Ensures(Implies(h > l, runs_bounds(ToSeq(Result().runs), ToSeq(Result().data), len(ToSeq(Result().data)))))
    Ensures(Implies(PROVE_CORRECT_RUNS and h > l, correct_runs(ToSeq(Result().runs), ToSeq(Result().data), len(ToSeq(Result().data)))))
    Ensures(len(ToSeq(Result().data)) == h - l)
    Ensures(Implies(PROVE_PERMUTATION, ToMS(ToSeq(Result().data)) == Old(ToMS(ToSeq(a).drop(l).take(h - l)))))
    Ensures(Implies(PROVE_RUNTIME, Acc(RT.steps) and RT.steps == Old(RT.steps) + log2(h - l) * (h - l)))

    data = []  # type: List[int]
    runs = []  # type: List[int]
    res = SR(runs, data)

    if l == h:
        return res
    if h - l == 1:
        if PROVE_RUNTIME:
            RT.steps += 1
        res.data.append(a[l])
        res.runs.append(len(res.data))
        Assert(Implies(PROVE_PERMUTATION, PSeq(a[l]) == ToSeq(a).drop(l).take(h - l)))
        return res
    m = l + (h - l) // 2
    res1 = msort(a, l, m)
    res2 = msort(a, m, h)
    s1 = ToSeq(a).drop(l).take(m - l)
    s2 = ToSeq(a).drop(m).take(h - m)
    s_all = ToSeq(a).drop(l).take(h - l)
    Assert(Implies(PROVE_PERMUTATION, s_all == s1 + s2))
    res = merge(res1, res2)
    Assert(Implies(PROVE_PERMUTATION, ToMS(ToSeq(res.data)) is Old(ToMS(ToSeq(a).drop(l).take(h - l)))))
    return res


@Pure
def log2(i: int) -> int:
    Requires(i >= 0)
    if i <= 1:
        return 1
    else:
        return 1 + log2(i // 2)
