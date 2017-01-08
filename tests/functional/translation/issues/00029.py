#:: IgnoreFile(29)
from py2viper_contracts.contracts import *


def test() -> None:
    r = [1, 2]
    Requires(Forall(r, lambda x: (foo(x), [])))
