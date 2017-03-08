from py2viper_contracts.contracts import *
from resources.sif_utils import input_high, input_low, sif_print
from typing import List

# TODO(shitz): Currently, we cannot test low/high indices in a meaningful way.
# The reason is that we need to specify some valid range for possible values of
# indices, but this is something that needs to be declassified (which is
# currently not implemented). Revisit this after declassification has been
# implemented.


# def low_idx() -> int:
#     Requires(Low())
#     Ensures(Low(Result()))
#     Ensures(Result() > 0 and Result() < 3)
#     return 1


# def high_idx() -> int:
#     Ensures(Result() > 0 and Result() < 3)
#     return 2


# def test_high_index() -> None:
#     Requires(Low())
#     x = high_idx()
#     y = low_idx()
#     l = [1, 2, 3]
#     sif_print(l[y])
#     #:: ExpectedOutput(call.precondition:assertion.false)
#     sif_print(l[x])


def high_ref() -> List[int]:
    Ensures(Acc(list_pred(Result())))
    return [1]


def low_ref() -> List[int]:
    Requires(Low())
    Ensures(Acc(list_pred(Result())))
    Ensures(Low(Result()))
    return [2]


def test_high_data() -> None:
    Requires(Low())
    x = input_high()
    y = input_low()
    l = [1, y]
    l.append(x)
    sif_print(l[1])
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(l[2])


@NotPreservingTL
def test_contains() -> None:
    Requires(Low())
    x = input_high()
    y = input_low()
    l = [1, 2, 3]
    if y in l:
        sif_print(0)
    if x in l:
        #:: ExpectedOutput(call.precondition:assertion.false)
        sif_print(1)


def test_high_ref() -> None:
    Requires(Low())
    h = high_ref()
    l = low_ref()
    l.append(1)
    sif_print(1)
    h.append(2)
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(2)
