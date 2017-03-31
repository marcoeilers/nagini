from nagini_contracts.contracts import *


def callee(a: bool) -> int:
    return a * 2


def test2() -> None:
    #:: ExpectedOutput(type.error:Argument 1 to "callee" has incompatible type "int"; expected "bool")
    a = callee(2)
