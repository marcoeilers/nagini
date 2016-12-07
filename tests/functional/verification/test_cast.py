from py2viper_contracts.contracts import *
from typing import cast


class C:
    def f(self, a: int = 15) -> None:
        pass


class D:
    pass


def m(l: List[object]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(len(l) > 1)
    #:: ExpectedOutput(application.precondition:assertion.false)
    cast(C, l[0]).f()


def m_2(l: List[object]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(len(l) > 1)
    Requires(isinstance(l[0], C))
    cast(C, l[0]).f()


def m_3(l: List[object]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(len(l) > 1)
    Requires(isinstance(l[0], C))
    c = cast(C, l[0])
    c.f()


def m_4(l: List[object]) -> None:
    Requires(Acc(list_pred(l)))
    Requires(len(l) > 1)
    Requires(isinstance(l[0], C))
    #:: ExpectedOutput(application.precondition:assertion.false)
    c = cast(D, l[0])