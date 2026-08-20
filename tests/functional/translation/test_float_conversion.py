# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f(x: int) -> float:
    #:: ExpectedOutput(unsupported:float() is currently only supported with arguments NaN and inf.)
    return float(x)
