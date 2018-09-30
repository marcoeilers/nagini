from nagini_contracts.contracts import *
from resources.sif_utils import input_high, input_low, sif_print
from typing import List


def high_ref() -> List[int]:
    Ensures(Acc(list_pred(Result())))
    return [1]


def low_ref() -> List[int]:
    Ensures(Acc(list_pred(Result())))
    Ensures(Low(Result()))
    return [2]


def test_high_data() -> None:
    Requires(LowEvent())
    x = input_high()
    y = input_low()
    l = [1, y]
    l.append(x)
    sif_print(l[1])
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(l[2])


def test_contains() -> None:
    Requires(LowEvent())
    x = input_high()
    y = input_low()
    l = [1, 2, 3]
    if y in l:
        sif_print(0)
    if x in l:
        #:: ExpectedOutput(call.precondition:assertion.false)
        sif_print(1)


def test_contains_2() -> None:
    Requires(LowEvent())
    x = input_high()
    l = [1, 2, 3]
    b = x in l
    sif_print(l[0])


def test_high_ref() -> None:
    Requires(LowEvent())
    h = high_ref()
    l = low_ref()
    l.append(1)
    sif_print(1)
    h.append(2)
    sif_print(2)


def test_high_index(low_idx: int, high_idx:int) -> None:
    Requires(LowEvent())
    Requires(low_idx >=0 and low_idx < 3)
    Requires(Low(low_idx))
    Requires(high_idx >=0 and high_idx < 3)
    Requires(Low(high_idx >= 0 and high_idx < 3))
    l = [1, 2, 3]
    sif_print(l[low_idx])
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(l[high_idx])
