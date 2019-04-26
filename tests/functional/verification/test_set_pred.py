# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


bla45 = ('bla', 45)


def main() -> None:
    asd46 = ('asd', 46)
    b23 = ('b', 23)
    dd2 = ('dd', 2)
    value = {asd46, b23, dd2}
    Assert(asd46 in value)
    Assert(dd2 in value)
    Assert(('blu', 45) not in value)
    append_bla_45(value)
    Assert(dd2 in value)
    Assert(len(value) == 4)
    Assert(bla45 in value)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(('muh', 45) in value)


def append_bla_45(l: Set[Tuple[str, int]]) -> None:
    Requires(Acc(set_pred(l)))
    Requires(len(l) > 1)
    Ensures(Acc(set_pred(l)))
    Ensures(Implies(Old(bla45 not in l), len(l) == Old(len(l)) + 1))
    Ensures(Forall(Old(l), lambda e: (e in l, [[e in l], [e in Old(l)]])))
    Ensures(bla45 in l)
    l.add(bla45)
