# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example adapted from https://bitbucket.org/covern/secc/src/master/examples/case-studies/
"""

from nagini_contracts.contracts import *
from typing import List, Tuple, Optional


class Elem:
    def __init__(self, key: int, value: int) -> None:
        self.key = key
        self.value = value
        self.next = None  # type: Optional[Elem]


@Pure
@ContractOnly
def global_label() -> int:
    pass

@Predicate
def ar(a: Optional[Elem], n: int) -> bool:
    return Implies(n > 0, Acc(a.key) and Acc(a.value) and Acc(a.next) and ar(a.next, n - 1))



@Predicate
def ar_sec(a: Optional[Elem], n: int) -> bool:
    return Implies(n > 0,
                   Acc(a.key) and Acc(a.value) and Acc(a.next) and Low(a.key) and Implies(a.key > global_label(), Low(a.value))
                   and ar_sec(a.next, n-1))

@Pure
def ar_sec_last(a: Optional[Elem], n: int) -> Optional[Elem]:
    Requires(n >= 0)
    Requires(ar_sec(a, n))
    return Unfolding(ar_sec(a, n), a if n == 0 else ar_sec_last(a.next, n - 1))

@Pure
def ar_sec_ith(a: Optional[Elem], n: int, i: int) -> Optional[Elem]:
    Requires(n >= 0)
    Requires(i >= 0 and i <= n)
    Requires(ar_sec(a, n))
    return Unfolding(ar_sec(a, n), a if i == 0 else ar_sec_ith(a.next, n - 1, i - 1))


def ar_sec_snoc(a: Optional[Elem], n: int) -> None:
    Requires(n >= 0)
    Requires(type(n) == int)
    Requires(Low(n))
    Requires(ar_sec(a, n))
    Requires(Acc(ar_sec_last(a, n).key) and Acc(ar_sec_last(a, n).value) and Acc(ar_sec_last(a, n).next))
    Requires(Low(ar_sec_last(a, n).key) and Implies(ar_sec_last(a, n).key > global_label(), Low(ar_sec_last(a, n).value)))
    Ensures(ar_sec(a, n + 1))
    Ensures(ar_sec_last(a, n + 1) is Old(ar_sec_last(a, n).next))
    if n == 0:
        Unfold(ar_sec(a, n))
        Fold(ar_sec(a.next, 0))
        Fold(ar_sec(a, 1))
    else:
        Unfold(ar_sec(a, n))
        ar_sec_snoc(a.next, n-1)
        Fold(ar_sec(a, n+1))


def ar_sec_join(a: Optional[Elem], n: int, m: int) -> None:
    Requires(n >= 0 and m >= 0)
    Requires(type(n) == int)
    Requires(type(m) == int)
    Requires(Low(n) and Low(m))
    Requires(ar_sec(a, n) and ar_sec(ar_sec_last(a, n), m))
    Ensures(ar_sec(a, n + m))
    Ensures(ar_sec_last(a, n + m) is Old(ar_sec_last(ar_sec_last(a, n), m)))
    if n == 0:
        Assert(ar_sec_last(a, n) is a)
        Assert(n + m is m)
        Unfold(ar_sec(a, n))

    else:
        Unfold(ar_sec(a, n))
        ar_sec_join(a.next, n-1, m)
        Fold(ar_sec(a, n+m))

SUCCESS = 0
FAILURE = 1


## 65 total, 8 non-spec

def lookup(elems: Optional[Elem], len: int, key: int) -> Tuple[int, int]:
    Requires(type(len) == int)
    Requires(ar_sec(elems, len))
    Requires(Low(len) and Low(key))
    Requires(len >= 0)
    Requires(type(len) == int)
    Ensures(ar_sec(elems, len))
    Ensures(Implies(Result()[0] == SUCCESS, Implies(key > global_label(), Low(Result()[1]))))
    Ensures(Implies(Result()[0] == FAILURE, Result()[1] == -1))
    Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)
    i = 0
    p = elems
    Fold(ar_sec(elems, 0))
    try:
        while i < len:
            Invariant(type(i) == int)
            Invariant(i >= 0 and i <= len)
            Invariant(Low(i) and LowExit())
            Invariant(ar_sec(p, len-i))
            Invariant(ar_sec(elems, i))
            Invariant(ar_sec_last(elems, i) is p)
            Unfold(ar_sec(p, len-i))
            if p.key is key:
                res = p.value
                Fold(ar_sec(p, len-i))
                return (SUCCESS, res)
            p = p.next
            ar_sec_snoc(elems, i)
            i += 1
    finally:
        ar_sec_join(elems, i, len - i)
    return (FAILURE, -1)


def split(a: Optional[Elem], i: int, n: int) -> None:
    Requires(type(i) == int and type(n) == int)
    Requires(Low(i))
    Requires(0 <= i and i <= n)
    Requires(ar_sec(a, n))
    Ensures(ar_sec(a, i) and ar_sec(ar_sec_last(a, i), n - i))
    Ensures(Old(ar_sec_ith(a, n, i)) is ar_sec_last(a, i))
    Ensures(Old(ar_sec_last(a, n)) is ar_sec_last(ar_sec_last(a, i), n - i))
    if i == 0:
        Fold(ar_sec(a, 0))
    else:
        Unfold(ar_sec(a, n))
        split(a.next, i - 1, n - 1)
        Fold(ar_sec(a, i))


def expose(a: Optional[Elem], i: int, n: int) -> None:
    Requires(type(i) == int and type(n) == int)
    Requires(Low(i))
    Requires(0 <= i and i < n)
    Requires(ar_sec(a, n))
    Ensures(ar_sec(a, i) )
    Ensures(Acc(ar_sec_last(a, i).key) and Acc(ar_sec_last(a, i).value) and Acc(ar_sec_last(a, i).next) and
            Low(ar_sec_last(a, i).key) and Implies(ar_sec_last(a, i).key > global_label(),
                                                   Low(ar_sec_last(a, i).value)))
    Ensures(ar_sec(ar_sec_last(a, i).next, n - i - 1))
    Ensures(Old(ar_sec_last(a, n)) is ar_sec_last(ar_sec_last(a, i).next, n - i - 1))
    if i == 0:
        Unfold(ar_sec(a, n))
        Fold(ar_sec(a, 0))
    else:
        Unfold(ar_sec(a, n))
        expose(a.next, i - 1, n - 1)
        Fold(ar_sec(a, i))

# 65 total, 10 non-spec

def cover(a: Optional[Elem], i: int, n: int) -> None:
    Requires(type(i) == int and type(n) == int)
    Requires(Low(i))
    Requires(0 <= i and i < n)
    Requires(ar_sec(a, i))
    Requires(Acc(ar_sec_last(a, i).key) and Acc(ar_sec_last(a, i).value) and Acc(ar_sec_last(a, i).next) and
             Low(ar_sec_last(a, i).key) and Implies(ar_sec_last(a, i).key > global_label(),
                                                    Low(ar_sec_last(a, i).value)))
    Requires(ar_sec(ar_sec_last(a, i).next, n - i - 1))
    Ensures(ar_sec(a, n))
    Ensures(Old(ar_sec_last(a, i)) is ar_sec_ith(a, n, i))
    Ensures(Old(ar_sec_last(a, i).next) is ar_sec_ith(a, n, i + 1))
    Ensures(Old(ar_sec_last(ar_sec_last(a, i).next, n - i - 1)) is ar_sec_last(a, n))
    if i == 0:
        old_next = ar_sec_last(a, i).next
        Unfold(ar_sec(a, 0))
        Fold(ar_sec(a, n))
        Assert(old_next is Unfolding(ar_sec(a, n), ar_sec_ith(a.next, n - 1, 0)))
    else:
        Unfold(ar_sec(a, i))
        cover(a.next, i - 1, n - 1)
        Fold(ar_sec(a, n))

# 22 total, 0 non-spec

def binsearch(elems: Optional[Elem], len: int, key: int) -> Tuple[int, int]:
    Requires(type(len) == int)
    Requires(len >= 0)
    Requires(ar_sec(elems, len))
    Requires(Low(len) and Low(key))
    Ensures(Low(Result()[0]))
    Ensures(Implies(Result()[0] == SUCCESS, Implies(key > global_label(), Low(Result()[1]))))
    Ensures(Implies(Result()[0] == FAILURE, Result()[1] == -1))
    Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)
    Ensures(Result()[0] == SUCCESS or Result()[0] == FAILURE)
    Ensures(ar_sec(elems, len))
    Ensures(ar_sec_last(elems, len) is Old(ar_sec_last(elems, len)))
    if len <= 0:
        return FAILURE, -1

    mid = len // 2
    expose(elems, mid, len)
    mid_el = ar_sec_last(elems, mid)
    k = mid_el.key
    if k == key:
        res = mid_el.value
        cover(elems, mid, len)
        return SUCCESS, res
    else:
        if len == 1:
            cover(elems, mid, len)
            return FAILURE, -1
        Assume(SplitOn(k > key))
        if k > key:
            cover(elems, mid, len)
            split(elems, mid-1, len)
            ret, outVal = binsearch(elems, mid-1, key)
            ar_sec_join(elems, mid-1, len-(mid-1))
            return ret, outVal
        else:
            mid_el_next = mid_el.next
            cover(elems, mid, len)
            Assert(mid_el_next is ar_sec_ith(elems, len, mid+1))
            split(elems, mid+1, len)
            ret, outVal = binsearch(mid_el_next, len - mid - 1, key)
            ar_sec_join(elems, mid + 1, len - (mid + 1))
            return ret, outVal

# 41 total, 17 non-spec


def sum_all(elems: Optional[Elem], len: int, key: int) -> int:
    Requires(type(len) == int)
    Requires(Low(len) and Low(key))
    Requires(len >= 0)
    Requires(ar_sec(elems, len))
    Ensures(ar_sec(elems, len))
    Ensures(Implies(key > global_label(), Low(Result())))
    sum = 0
    p = elems
    i = 0
    Fold(ar_sec(elems, 0))
    while i < len:
        Invariant(type(i) == int)
        Invariant(i >= 0 and i <= len)
        Invariant(Implies(key > global_label(), Low(sum)) and Low(i))
        Invariant(ar_sec(p, len - i))
        Invariant(ar_sec(elems, i))
        Invariant(p is ar_sec_last(elems, i))
        Unfold(ar_sec(p, len - i))
        if p.key is key:
            sum += p.value
        p = p.next
        ar_sec_snoc(elems, i)
        i += 1
    ar_sec_join(elems,i,len-i)
    return sum

# 26 total, 10 non-spec


def sum_all_rec(p: Optional[Elem], len: int, key: int, init: int) -> int:
    Requires(type(len) == int)
    Requires(ar_sec(p, len))
    Requires(Low(len) and Low(key))
    Requires(len >= 0)
    Requires(Implies(key > global_label(), Low(init)))
    Ensures(ar_sec(p, len))
    Ensures(Implies(key > global_label(), Low(Result())))
    if len > 0:
        Unfold(ar_sec(p, len))
        if p.key == key:
            s = sum_all_rec(p.next, len - 1, key, init + p.value)
            Fold(ar_sec(p, len))
            return s
        else:
            s = sum_all_rec(p.next, len - 1, key, init)
            Fold(ar_sec(p, len))
            return s
    else:
        return init

# 20 total, 10 non-spec


def remove_all(elems: Optional[Elem], len: int, key: int) -> None:
    Requires(type(len) == int)
    Requires(ar_sec(elems, len))
    Requires(Low(len) and Low(key) and len >= 0)
    Ensures(ar_sec(elems, len))
    i = 0
    p = elems
    Fold(ar_sec(elems, 0))
    while i < len:
        Invariant(type(i) == int)
        Invariant(Low(i) and i >= 0 and i <= len)
        Invariant(ar_sec(elems, i))
        Invariant(ar_sec(p, len - i))
        Invariant(p is ar_sec_last(elems, i))
        Unfold(ar_sec(p, len - i))
        if p.key == key:
            p.value = 0
        p = p.next
        ar_sec_snoc(elems, i)
        i += 1
    Unfold(ar_sec(p, len - i))

# 21 total, 8 non-spec
