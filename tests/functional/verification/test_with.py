# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple, Optional


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

    def __exit__(self, t: type, e: Optional[Exception], tb: Optional[object]) -> int:
        Requires(Acc(self.value))
        Ensures(Acc(self.value) and self.value == Old(self.value) + 7)
        self.value += 7
        return 7


class MyException(Exception):
    pass


class NoLockExOnly:

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
        Requires(isinstance(e, MyException))
        Ensures(Acc(self.value) and self.value == Old(self.value) + 7)
        self.value += 7
        return 7


class NoLockNoEx:

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

    def __exit__(self, t: type, e: Optional[Exception], tb: Optional[object]) -> int:
        Requires(e is None)
        Requires(tb is None)
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


def client_exonly() -> NoLockExOnly:
    nl = NoLockExOnly()
    #:: ExpectedOutput(call.precondition:assertion.false)
    with nl as v:
        nl.value += v
    return nl


def client_exonly_2() -> NoLockExOnly:
    nl = NoLockExOnly()
    #:: ExpectedOutput(call.precondition:assertion.false)
    with nl as v:
        return nl


def client_exonly_3() -> NoLockExOnly:
    Ensures(False)
    Exsures(Exception, True)
    nl = NoLockExOnly()
    #:: ExpectedOutput(call.precondition:assertion.false)
    with nl as v:
        raise Exception()


def client_exonly_4() -> NoLockExOnly:
    nl = NoLockExOnly()
    #:: ExpectedOutput(exhale.failed:assertion.false)
    with nl as v:
        raise MyException()


def client_exonly_5() -> NoLockExOnly:
    Ensures(False)
    Exsures(MyException, True)
    nl = NoLockExOnly()
    with nl as v:
        raise MyException()


def client_noex() -> NoLockNoEx:
    nl = NoLockNoEx()
    with nl as v:
        nl.value += v
    return nl


def client_noex_2() -> NoLockNoEx:
    nl = NoLockNoEx()
    with nl as v:
        return nl


def client_noex_3() -> NoLockNoEx:
    nl = NoLockNoEx()
    #:: ExpectedOutput(call.precondition:assertion.false)
    with nl as v:
        raise MyException()


def client_noex_4() -> NoLockNoEx:
    Ensures(False)
    Exsures(MyException, True)
    nl = NoLockNoEx()
    #:: ExpectedOutput(call.precondition:assertion.false)
    with nl as v:
        raise MyException()