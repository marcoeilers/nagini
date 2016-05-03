from py2viper_contracts.contracts import *
from typing import Tuple


def something(s: str, a: Tuple[str, int]) -> Tuple[str, str, int]:
    c = s + 'asdasd'
    b = (c, a[0])


def something_else() -> str:
    a, b, c = something('asd', ('assaa', 15))
    return a
