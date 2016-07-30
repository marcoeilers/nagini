from py2viper_contracts.contracts import *
from typing import Tuple


def main() -> None:
    value = {('asd', 46), ('b', 23), ('dd', 2)}
    Assert(('asd', 46) in value)
    Assert(('dd', 2) in value)
    Assert(('bla', 45) not in value)
    append_bla_45(value)
    #:: UnexpectedOutput(assert.failed:assertion.false, /py2viper/issue/48/, carbon)
    Assert(('dd', 2) in value)
    Assert(len(value) == 4)
    Assert(('bla', 45) in value)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(('muh', 45) in value)


def append_bla_45(l: Set[Tuple[str, int]]) -> None:
    Requires(Acc(set_pred(l)))
    Requires(len(l) > 1)
    Ensures(Acc(set_pred(l)))
    Ensures(Implies(Old(('bla', 45) not in l), len(l) == Old(len(l)) + 1))
    Ensures(Forall(Old(l), lambda e: (e in l, [[e in l], [e in Old(l)]])))
    Ensures(('bla', 45) in l)
    l.add(('bla', 45))
