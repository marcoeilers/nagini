from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock

from typing import Tuple

def declassify(x: int, y: int) -> int:
    Requires(Low(x))
    Requires(Low(y == 0))
    Ensures(Low(Result()))
    z = x + y
    if z != x:
        Declassify(y)
    return z


@ContractOnly
def ask_user1(x: int) -> bool:
    Ensures(Low(Result()))
    Ensures(Implies(Result(), Low(x)))


def do_declassify1(x: int) -> int:
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    r = 0
    if ask_user1(x):
        r = x
    return r


@ContractOnly
def ask_user2(x: int) -> bool:
    Ensures(Low(Result()))


def do_declassify2(x: int) -> int:
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    r = 0
    b = ask_user2(x)
    if b:
        Declassify(x)
    if b:
        r = x
    return r


@Pure
@ContractOnly
def safe_to_declassify(x: int) -> bool:
    pass


@ContractOnly
def ask_user(x: int) -> bool:
    Ensures(Low(Result()))
    Ensures(Implies(Result(), safe_to_declassify(x)))


def do_declassify(x: int) -> int:
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    r = 0
    if ask_user(x):
        if safe_to_declassify(x):
            Declassify(x)
        r = x
    return r


def do_declassify_without_asking(x: int) -> int:
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    r = 0
    if safe_to_declassify(x):
        Declassify(x)
    r = x
    return r


def declassify_by_attrition(x: int) -> int:
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    while 1 != 0:
        pass
    if safe_to_declassify(x):
        Declassify(x)
    return x


Pair = Tuple[int, bool]

@Predicate
def io_trace() -> bool:
    return True

@Pure
@ContractOnly
def io_trace_seq() -> PSeq[Pair]:
    Requires(io_trace())

@Pure
@ContractOnly
def safe_to_declassify_2(x: int) -> bool:
    Requires(io_trace())
    Ensures(Result() == (len(io_trace_seq()) > 0 and io_trace_seq()[0][0] is x and io_trace_seq()[0][1]))


@ContractOnly
def ask_user3(x: int) -> bool:
    Requires(io_trace())
    Ensures(io_trace())
    Ensures(io_trace_seq() == PSeq((x, Result())) + Old(io_trace_seq()))
    Ensures(Low(Result()))


def do_declassify3(x: int) -> int:
    Requires(io_trace())
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    Ensures(io_trace())
    r = 0
    res = ask_user3(x)
    if res:
        Assert(safe_to_declassify_2(x))
        Declassify(x)
        r = x
    return r


@Predicate
def avg_state_correct(s: int, c: int, xs: PSeq[int]) -> bool:
    return (Low(len(xs) == 0) and
            Implies(len(xs) == 0, s == 0 and c == 0) and
            Implies(len(xs) > 0, avg_state_correct(s-xs[0], c-1, xs.drop(1))))


class AvgState:
    def __init__(self, count: int, sum: int, min: int) -> None:
        self.count = count
        self.sum = sum
        self.min = min

class StateLock(Lock[AvgState]):

    @Predicate
    def invariant(self) -> bool:
        return (consumed_inputs() and
                Acc(self.get_locked().count) and
                self.get_locked().count >= 0 and
                Low(self.get_locked().count) and
                Acc(self.get_locked().min) and
                self.get_locked().min > 0 and
                Low(self.get_locked().min) and
                Acc(self.get_locked().sum) and
                avg_state_correct(self.get_locked().sum, self.get_locked().count, get_consumed_inputs()))

DUMMY = 0

@Predicate
def consumed_inputs() -> bool:
    return Low(DUMMY)

@Pure
@ContractOnly
def get_consumed_inputs() -> PSeq[int]:
    Requires(consumed_inputs())

@Pure
def ssum(xs: PSeq[int]) -> int:
    if len(xs) == 0:
        return 0
    return xs[0] + ssum(xs.drop(1))

@Predicate
def avg_safe_to_declassify(x: int, st: AvgState) -> bool:
    return (consumed_inputs() and
            Low(len(get_consumed_inputs())) and
            Acc(st.min) and
            len(get_consumed_inputs()) > st.min and
            Low(st.min) and st.min > 0 and
            x == (ssum(get_consumed_inputs()) // len(get_consumed_inputs())))

@ContractOnly
def avg_get_input() -> int:
    Requires(consumed_inputs())
    Ensures(consumed_inputs())
    Ensures(get_consumed_inputs() == PSeq(Result()) + Old(get_consumed_inputs()))


def avg_sum_thread(st: AvgState, l: StateLock) -> None:
    Requires(l.get_locked() is st and Low(l))
    l.acquire()
    i = avg_get_input()
    st.count += 1
    st.sum += 1
    l.release()

def avg_inc_min_thread(st: AvgState, l: StateLock) -> None:
    Requires(l.get_locked() is st and Low(l))
    l.acquire()
    st.min += 1
    l.release()


def avg_declass_thread(st: AvgState, l: StateLock) -> None:
    Requires(l.get_locked() is st and Low(l))
    l.acquire()
    if st.count > st.min:
        avg = st.sum // st.count
        Fold(avg_safe_to_declassify(avg, st))
        Declassify(avg)
        Unfold(avg_safe_to_declassify(avg, st))
    l.release()