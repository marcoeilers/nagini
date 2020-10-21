from nagini_contracts.contracts import *


def add_zero_incorrect(i: int, secret: int) -> int:
    Requires(Low(i))
    Ensures(Low(Result()))
    if secret == 0:
        return i + 0
    return i


def add_zero_correct(i: int, secret: int) -> int:
    Requires(Low(i))
    Ensures(LowVal(Result()))
    if secret == 0:
        return i + 0
    return i