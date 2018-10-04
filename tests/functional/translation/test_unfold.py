from nagini_contracts.contracts import Unfold


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.call)
    Unfold(True)