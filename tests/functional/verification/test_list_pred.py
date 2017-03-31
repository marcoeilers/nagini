from nagini_contracts.contracts import *
from typing import Tuple


def main() -> None:
    value = [('asd', 46), ('b', 23), ('dd', 2)]
    Assert(value[0][0] == 'asd')
    Assert(value[2][0] == 'dd')
    s = get_second(value)
    Assert(s == 23)
    Assert(value[2][0] == 'dd')
    append_bla_45(value)
    Assert(value[2][0] == 'dd')
    Assert(get_second(value) == 23)
    Assert(len(value) == 4)
    Assert(value[3][0] == 'bla')
    # TODO: without assertions above, this assertion fails (sometimes)
    Assert(value[2][0] == 'dd')
    Assert(value[3][1] == 45)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(value[0][1] == 47)


def get_second(l: List[Tuple[str, int]]) -> int:
    Requires(Acc(list_pred(l), 1/10))
    Requires(len(l) > 1)
    Ensures(Acc(list_pred(l), 1/10))
    # TODO: why is this necessary?
    Ensures(len(l) == Old(len(l)))
    Ensures(Result() == l[1][1])
    return l[1][1]


bla45 = ('bla', 45)


def append_bla_45(l: List[Tuple[str, int]]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(len(l) > 1)
    Ensures(Acc(list_pred(l)))
    Ensures(len(l) == Old(len(l)) + 1)
    Ensures(Forall(range(0, Old(len(l))),
                   lambda i: (l[i] is Old(l[i]), [[l[i]], [Old(l[i])]])))
    Ensures(l[len(l) - 1] is bla45)
    l.append(bla45)
