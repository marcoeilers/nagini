from py2viper_contracts.contracts import *
from resources.sif_utils import input_high, input_low, sif_print


@NotPreservingTL
def fig1a() -> None:
    Requires(Low())
    x = input_high()
    if x < 1234:
        x = 0
    y = x
    #:: ExpectedOutput(call.precondition:assertion.false) | ExpectedOutput(carbon)(call.precondition:assertion.false)
    sif_print(y)


def fig1a_low() -> None:
    Requires(Low())
    x = input_low()
    if x < 1234:
        sif_print(0)
    y = x
    sif_print(y)


@NotPreservingTL
def fig2a() -> None:
    x = input_high()
    if x == 1:
        l = 42
    else:
        l = 17
    l = 0
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(l)


@Pure
def f(x: int) -> int:
    return x + 42


def fig2b_low() -> None:
    Requires(Low())
    h = input_high()
    l = input_low()
    x = f(h)
    y = f(l)
    sif_print(y)


def fig2b() -> None:
    Requires(Low())
    h = input_high()
    l = input_low()
    x = f(h)
    y = f(l)
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(x)
