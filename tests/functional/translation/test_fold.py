from nagini_contracts.contracts import Fold


def client() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.call)
    Fold(True)