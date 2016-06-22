#:: IgnoreFile(/py2viper/issue/19/)
from py3viper_contracts.contracts import *


@Pure
def identity(a: int) -> int:
    return a

def test_list_3() -> None:
    r = [1, 2, 3]
    Assert(Forall(r, lambda i: (identity(i) > 0, [])))
