from nagini_contracts.contracts import *


def test_list_3(r: List[int]) -> None:
    #:: ExpectedOutput(not.wellformed:insufficient.permission)|UnexpectedOutput(carbon)(not.wellformed:insufficient.permission, 168)
    Requires(Forall(r, lambda i: (i > 0, [])))

    a = 3
