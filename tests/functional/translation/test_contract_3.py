from nagini_contracts.contracts import Assert


def test() -> None:
    #:: ExpectedOutput(invalid.program:invalid.contract.position)
    Assert(Assert(True))
