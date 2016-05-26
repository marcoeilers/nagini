from py2viper_contracts.contracts import *
from typing import List, Tuple


def main() -> None:
    value = [('asd', 45), ('b', 23), ('dd', 2)]
    s = get_second(value)
    Assert(s == 23)
    append_bla_45(value)
    Assert(get_second(value) == 23)
    Assert(len(value) == 4)
    Assert(value[3][0] == 'bla')


def get_second(l: List[Tuple[str, int]]) -> int:
    Requires(Acc(list_pred(l), 1/10))
    Requires(len(l) > 1)
    Ensures(Acc(list_pred(l), 1/10))
    Ensures(len(l) == Old(len(l)))  # TODO: this should not be necessary
    Ensures(Result() == l[1][1])
    return l[1][1]


def append_bla_45(l: List[Tuple[str, int]]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(len(l) > 1)
    Ensures(Acc(list_pred(l)))
    Ensures(len(l) == Old(len(l)) + 1)
    Ensures(Forall(range(0, Old(len(l)) - 1),
                   lambda i: (l[i] == Old(l[i]), [[l[i]], [Old(l[i])]])))
    Ensures(l[len(l) - 1] == ('bla', 45))
    l.append(('bla', 45))