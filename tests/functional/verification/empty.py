# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from nagini_contracts.contracts import Requires, Ensures, Result, Acc, list_pred, Assert, dict_pred, PSeq, ToSeq, Pure, Predicate, Unfold
from typing import List, Dict


class Cell:
    def __init__(self) -> None:
        self.v = 5
        self.v2 = 10

    def urgh(self, a: int) -> int:
        Requires(a > 9)
        Ensures(Result() > 17)
        return a + 7

    @Predicate
    def classP(self, j: int) -> bool:
        return Acc(self.v) and self.v > 0 and j / self.v > 0


class SubCell(Cell):

    def urgh(self, a: int) -> int:
        Requires(a > 9)
        Ensures(Result() > 15)
        return a + 8

    @Predicate
    def classP(self, j: int) -> bool:
        return j > 2

def get_me_hennimore(i: int) -> int:
    Ensures(Result() > i and Result() < i+10)
    return i+5

a = 12
a = get_me_hennimore(5)
b = 1
b = 7 // (a - 7)



@Predicate
def P(c: Cell, j: int) -> bool:
    return Acc(c.v) and c.v > 0 and j / c.v > 0

# @Pure
# def double(c: Cell, i: int) -> int:
#     Requires(Acc(c.v))
#     Ensures(Result() > 0)
#     a = c.v * 2
#     return a + i


def test_ce(a: int, b: bool, c3: Cell, c: int, re: Cell, re2: Cell, myi: int, l: List[int], d: Dict[int, int], ls: PSeq[int]) -> int:
    Requires(P(c3, 25))
    Requires(list_pred(l) and len(l) > 8 and ls is ToSeq(l))
    Requires(dict_pred(d) and len(d) > 0 and a not in d)
    Requires(a > 4)
    Requires(Acc(re.v) and re.v == a and Acc(re.v2))
    # Requires(Acc(re2.v) and re2.v == 123456 and isinstance(re2, SubCell))
    Requires(isinstance(re2, SubCell) and re2.classP(500))
    Ensures(Result() > 10)

    Unfold(P(c3, 25))
    d[a] = a
    d[a + 1] = a + 1
    asdddd = len(d)
    # Assert(re is not re2)
    l.append(2)
    asd = len(l)
    wowastring = "asd"
    l.append(2)
    asdd = len(l)
    asdd += 1
    res = 7 + b
    if not b:
        res = 7
        # TODO: cannot deal with undefined variables yet.
        uhuhu = 89
    elif c == 45:
        res = a
    re.v = 34
    c = 888 # // myi
    d = {1: 2, 7: 9}
    aset = {re, re2}
    # Assert(len(aset) == 2)
    return 4 + res