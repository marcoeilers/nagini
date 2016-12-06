#:: IgnoreFile(33)
from py2viper_contracts.contracts import *


def callee(a: int) -> int:
    return a * 2


def test2() -> None:
    a = callee(True)
