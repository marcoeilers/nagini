#:: IgnoreFile(29)
from nagini_contracts.contracts import *


def test() -> None:
    r = [1, 2]
    Requires(Forall(r, lambda x: (foo(x), [])))
