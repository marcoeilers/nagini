from py2viper_contracts.contracts import *


def test_list_3(r: List[int]) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)|UnexpectedOutput(carbon)(application.precondition:insufficient.permission, 168)
    Requires(Forall(r, lambda i: (i > 0, [])))

    a = 3
