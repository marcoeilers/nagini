from py2viper_contracts.contracts import *
from typing import Tuple


class NoLock:

    def __init__(self) -> None:
        Ensures(Acc(self.value))  # type: ignore
        Ensures(self.value == 4)  # type: ignore
        self.value = 4

    def __enter__(self) -> int:
        Requires(Acc(self.value))
        Ensures(Acc(self.value) and self.value == Old(self.value) + 5)
        Ensures(Result() == 9)
        self.value += 5
        return 9

    def __exit__(self, t: type, e: Exception, tb: object) -> int:
        Requires(Acc(self.value))
        Ensures(Acc(self.value) and self.value == Old(self.value) + 7)
        self.value += 7
        return 7


def client() -> NoLock:
    Ensures(Acc(Result().value) and Result().value == 25)
    nl = NoLock()
    with nl as v:
        nl.value += v
    return nl


def client_2() -> NoLock:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(Result().value) and Result().value == 24)
    nl = NoLock()
    with nl as v:
        nl.value += v
    return nl


def client_3() -> Tuple[NoLock, int]:
    Ensures(Acc(Result()[0].value) and Result()[0].value == 16)
    Ensures(Result()[1] == 18)
    nl = NoLock()
    with nl as v:
        return (nl, nl.value + v)


def client_4() -> Tuple[NoLock, int]:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(Result()[0].value) and Result()[0].value == 15)
    Ensures(Result()[1] == 18)
    nl = NoLock()
    with nl as v:
        return (nl, nl.value + v)