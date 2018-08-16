from nagini_contracts.contracts import Unfolding


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.call)
    a = Unfolding(True, 45)