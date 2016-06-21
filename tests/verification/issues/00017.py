from py2viper_contracts.contracts import *


def a() -> None:
    a = [1, 2]
    b = [True]
    Assert(Forall(a, lambda x: (x > 0, [])) and Forall(b, lambda x: (x, [])))