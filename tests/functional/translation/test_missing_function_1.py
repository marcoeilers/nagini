#:: IgnoreFile(29)
from py2viper_contracts.contracts import *
from typing import List


def test(r: List[int]) -> None:
    Requires(Forall(r, lambda x: (foo(x), [])))
