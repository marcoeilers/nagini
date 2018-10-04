from nagini_contracts.contracts import *


def test() -> None:
    r = [1, 2]
    #:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)
    Requires(Forall(r, lambda x: (foo(x), [])))
