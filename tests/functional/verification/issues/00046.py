from py2viper_contracts.contracts import *


def test_list_3(r: List[int]) -> None:
    #:: ExpectedOutput(application.precondition:insufficient.permission)
    Requires(Forall(r, lambda i: (i > 0, [])))

    a = 3
