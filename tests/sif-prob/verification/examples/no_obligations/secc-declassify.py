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
    # should fail
    Ensures(Low(Result()))
    Ensures(Result() == x or Result() == 0)
    r = 0
    # if safe_to_declassify(x):
    Declassify(x if safe_to_declassify(x) else 0)
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

@Predicate
def safe_to_declassify_2() -> bool:
    return io_trace() and len(io_trace_seq()) > 0

@Pure
def safe_to_declassify_2_x() -> int:
    Requires(safe_to_declassify_2())
    return Unfolding(safe_to_declassify_2(), io_trace_seq()[0][0])


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
        Fold(safe_to_declassify_2())
        Declassify(x)
        r = x
        Unfold(safe_to_declassify_2())
    return r


@Predicate
def avg_state_correct(s: int, c: int, xs: PSeq[int]) -> bool:
    return (Low(len(xs) == 0) and
            Implies(len(xs) is 0, s is 0 and c is 0) and
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
                Low(self.get_locked().count) and type(self.get_locked().count) == int and
                Acc(self.get_locked().min) and
                self.get_locked().min > 0 and
                Low(self.get_locked().min) and
                Acc(self.get_locked().sum) and type(self.get_locked().sum) == int and
                avg_state_correct(self.get_locked().sum, self.get_locked().count, consumed_inputs_inps()))

"""

/* the invariant protected by the lock */
_(predicate avg_inv(struct avg_state *st)
  exists int c, int s, int m, list<int> inps. consumed_inputs(;inps) &&
  &st->count |-> c && c :: low && c >= 0 &&
  &st->sum |-> s && &st->min |-> m && m > 0 && m :: low &&
  avg_state_correct(;s, c, inps)  
)

"""
DUMMY = 1

@Predicate
def consumed_inputs() -> bool:
    return Low(1) # workaround for bug in the trafo?

@Pure
@ContractOnly
def consumed_inputs_inps() -> PSeq[int]:
    Requires(Rd(consumed_inputs()))

@Pure
def ssum(xs: PSeq[int]) -> int:
    if len(xs) == 0:
        return 0
    return xs[0] + ssum(xs.drop(1))

"""
_(predicate avg_state_correct2(;int s, int c, list<int> xs)
  c :: low && c == length(xs) && s == ssum(xs))
"""
@Predicate
def avg_state_correct2(s: int, c: int, xs: PSeq[int]) -> bool:
    return Low(c) and c is len(xs) and s is ssum(xs)

@Predicate
def avg_safe_to_declassify(x: int, st: AvgState) -> bool:
    return (consumed_inputs() and
            Low(len(consumed_inputs_inps())) and
            Acc(st.min) and
            len(consumed_inputs_inps()) > st.min and
            Low(st.min) and st.min > 0 and
            x == (ssum(consumed_inputs_inps()) // len(consumed_inputs_inps())))

"""

/* The security policy. */
_(predicate avg_safe_to_declassify(int x, struct avg_state *st; list<int> inps)
  exists int c, int s, int m. consumed_inputs(;inps) &&
  c :: low && c == length(inps) && s == ssum(inps) &&
  &st->min |-> m && m > 0 && m :: low &&
  x == (s / c) && c > m
)
"""

@ContractOnly
def avg_get_input() -> int:
    Requires(consumed_inputs())
    Ensures(consumed_inputs())
    Ensures(consumed_inputs_inps() == PSeq(Result()) + Old(consumed_inputs_inps()))


def avg_sum_thread(st: AvgState, l: StateLock) -> None:
    Requires(l.get_locked() is st and Low(l))
    l.acquire()
    old_inps = consumed_inputs_inps()
    old_sum = st.sum
    old_count = st.count
    Assert(avg_state_correct(st.sum, st.count, old_inps))
    i = avg_get_input()
    Assert(consumed_inputs_inps().drop(1) == old_inps)
    st.count += 1
    st.sum += i
    Assert(st.sum - consumed_inputs_inps()[0] is old_sum)
    Assert(st.count - 1 is old_count)
    Assert(avg_state_correct(st.sum - consumed_inputs_inps()[0], st.count - 1, consumed_inputs_inps().drop(1)))
    Fold(avg_state_correct(st.sum, st.count, consumed_inputs_inps()))
    l.release()

"""
/* the thread that reads, counts and sums the inputs */
void avg_sum_thread(){
  struct avg_state * st = avg_lock();
  _(unfold avg_inv(st))
  _(assert exists list<int> inps. consumed_inputs(;inps))
  int i = avg_get_input();
  _(apply sum_lemma(st->sum, st->count, inps, i);)
  st->count += 1;
  st->sum += i;
  _(fold avg_inv(st))  
  avg_unlock(st);
}
"""

def avg_inc_min_thread(st: AvgState, l: StateLock) -> None:
    Requires(l.get_locked() is st and Low(l))
    l.acquire()
    st.min += 1
    l.release()

"""
/* the thread that increments the 'min' variable */
void avg_inc_min_thread(){
  struct avg_state * st = avg_lock();
  _(unfold avg_inv(st))
  st->min += 1;
  _(fold avg_inv(st))  
  avg_unlock(st);
}
"""

def avg_state_correct_implies(s: int, c: int, xs: PSeq[int]) -> None:
    Requires(avg_state_correct(s, c, xs))
    Requires(type(c) == int and type(s) == int)
    Ensures(avg_state_correct2(s, c, xs))
    Unfold(avg_state_correct(s, c, xs))
    if len(xs) == 0:
        Fold(avg_state_correct2(s, c, xs))
    else:
        Assert(avg_state_correct(s - xs[0], c - 1, xs.drop(1)))
        y = xs[0]
        ys = xs.drop(1)
        avg_state_correct_implies(s - y, c - 1, ys)
        Unfold(avg_state_correct2(s - y, c - 1, ys))
        Assert(c == len(xs))
        Assert(c is len(xs))
        Fold(avg_state_correct2(s, c, xs))
"""
void avg_state_correct_implies(int s, int c, list<int> xs)
_(requires avg_state_correct(;s,c,xs))
_(ensures avg_state_correct2(;s,c,xs))
_(lemma)
{
  _(unfold avg_state_correct(;s,c,xs))
  if (xs == nil){
    _(fold avg_state_correct2(;s,c,nil))
  }else{
    _(assert exists int y, list<int> ys. xs == cons(y,ys))
    _(apply avg_state_correct_implies(s-y,c-1,ys);)
    _(unfold avg_state_correct2(;s-y,c-1,ys))
    _(fold avg_state_correct2(;s,c,xs))      
  }
}

"""

def avg_state_correct2_implies(s: int, c: int, xs: PSeq[int]) -> None:
    Requires(avg_state_correct2(s, c, xs))
    Ensures(avg_state_correct(s, c, xs))
    Unfold(avg_state_correct2(s, c, xs))
    if len(xs) == 0:
        Fold(avg_state_correct(s, c, xs))
    else:
        y = xs[0]
        ys = xs.drop(1)
        Assert(len(ys) == len(xs) - 1)
        Fold(avg_state_correct2(s - y, c - 1, ys))
        avg_state_correct2_implies(s - y, c - 1, ys)
        Fold(avg_state_correct(s, c, xs))

"""
{
  _(unfold avg_state_correct2(;s,c,xs))
  length_low_nil_low(xs);
  if (xs == nil){
    _(fold avg_state_correct(;s,c,nil))
  }else{
    _(assert exists int y, list<int> ys. xs == cons(y,ys))
      
    // little bit annoying deriving length(ys) :: low
    _(assert length(xs) == length(cons(y,ys)))
    _(assert length(xs) == 1 + length(ys))      

    _(fold avg_state_correct2(;s-y,c-1,ys))
    avg_state_correct2_implies(s-y,c-1,ys);
    _(fold avg_state_correct(;s,c,xs))      
  }
}
"""

def avg_declass_thread(st: AvgState, l: StateLock) -> None:
    Requires(l.get_locked() is st and Low(l))
    l.acquire()
    if st.count > st.min:
        avg = st.sum // st.count
        s = st.sum
        c = st.count
        avg_state_correct_implies(s, c, consumed_inputs_inps())
        Unfold(avg_state_correct2(st.sum, st.count, consumed_inputs_inps()))
        Fold(avg_safe_to_declassify(avg, st))
        Declassify(avg)
        Unfold(avg_safe_to_declassify(avg, st))
        inps = consumed_inputs_inps()
        Fold(avg_state_correct2(s, c, inps))
        avg_state_correct2_implies(s, c, inps)
    l.release()


"""

/* the thread that does the declassification */
void avg_declass_thread(){
  struct avg_state * st = avg_lock();
  _(unfold avg_inv(st))
    _(assert exists list<int> inps. consumed_inputs(;inps))
  if (st->count > st->min){
    int avg = st->sum / st->count;
    _(assert  consumed_inputs(;inps))
    _(assert exists int c, int s. &st->sum |-> s && &st->count |-> c)
    _(apply avg_state_correct_implies(s, c, inps);)
    _(unfold avg_state_correct2(;s, c, inps))
      
    _(fold avg_safe_to_declassify(avg,st;inps))
    _(assume (avg :: low))
      
    _(unfold avg_safe_to_declassify(avg,st;inps))
    _(fold avg_state_correct2(;s, c, inps))
    _(apply avg_state_correct2_implies(s, c, inps);)
    _(fold avg_inv(st))
  }else{
    _(fold avg_inv(st))
  }
  avg_unlock(st);
}
"""