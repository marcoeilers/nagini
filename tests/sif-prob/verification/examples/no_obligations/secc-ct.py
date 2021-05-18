# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example adapted from https://bitbucket.org/covern/secc/src/master/examples/case-studies/
"""

from nagini_contracts.contracts import *
from typing import List

@Pure
def abs_choose(c: bool, a: int, b: int) -> int:
    if c:
        return a
    return b


def choose_ct(c: bool, a: int, b: int) -> int:
    Ensures(Result() == abs_choose(c, a, b))
    return (c * a) + ((1-c) * b)


def not_ct(a: bool) -> int:
    Ensures(Result() == (not a))
    return 1 - a


def max_ct(a: int, b: int) -> int:
    Ensures(Result() == (a if a>b else b))
    return choose_ct(a > b, a, b)


def min_ct(a: int, b: int) -> int:
    Ensures(Result() == (a if a<b else b))
    return choose_ct(a < b, a, b)


def memcmp_ct(l1: List[int], l2: List[int], i: int, n: int) -> int:
    Requires(Acc(list_pred(l1)) and Acc(list_pred(l2)))
    Requires(n >= 0 and i >= 0)
    Requires(Low(n) and len(l1) == i + n and len(l2) == i + n)
    Ensures(Acc(list_pred(l1)) and Acc(list_pred(l2)))
    Ensures(ToSeq(l1) is Old(ToSeq(l1)) and ToSeq(l2) is Old(ToSeq(l2)))
    Ensures(Result() == (not (ToSeq(l1).drop(i) == ToSeq(l2).drop(i))))
    if n != 0:
        a = l1[i]
        b = l2[i]

        # Need reference comparison, otherwise list contents are technically not equal.
        c = a is not b
        d = memcmp_ct(l1, l2, i + 1, n - 1)
        m = max_ct(c, d)
        return m
    else:
        return False

@Pure
def abs_max_list(s: PSeq[int]) -> int:
    Requires(len(s) > 0)
    if len(s) == 1:
        return s[0]
    else:
        return max(s[0], abs_max_list(s.drop(1)))


def max_list(l: List[int], i: int, n: int) -> int:
    Requires(Acc(list_pred(l)))
    Requires(n > 0 and i >= 0)
    Requires(Low(n) and len(l) == i + n)
    Ensures(Acc(list_pred(l)))
    Ensures(ToSeq(l) is Old(ToSeq(l)))
    Ensures(Result() == abs_max_list(ToSeq(l).drop(i)))

    if n == 1:
        res = l[i]
        return res
    else:
        m = max_list(l, i + 1, n - 1)
        Assert(ToSeq(l).drop(i).drop(1) == ToSeq(l).drop(i + 1))
        res = max_ct(l[i], m)
        return res


def password_checker(guess: List[int], stored_password: List[int]) -> int:
    Requires(Acc(list_pred(guess)) and Acc(list_pred(stored_password)))
    Requires(Low(ToSeq(guess) == ToSeq(stored_password)))
    Requires(len(stored_password) == len(guess) and Low(len(guess)))
    Ensures(Acc(list_pred(guess)) and Acc(list_pred(stored_password)))
    Ensures(LowVal(Result()))

    return memcmp_ct(guess, stored_password, 0, len(guess))
