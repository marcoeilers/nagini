from py2viper_contracts.contracts import *

# Helper functions to generate high/low input.
def input_high() -> int:
    return 42


def input_low() -> int:
    Requires(Low())
    Ensures(Low(Result()))
    return 42


def sif_print(x: int) -> None:
    Requires(Low(x))
    pass


@NotPreservingTL
def fig1a() -> None:
    Requires(Low())
    x = input_high()
    # The if statement below makes carbon throw two precondition violated
    # exceptions, since both !tl and y == y_p are false. Silicon only produces
    # one exception. Our test framework cannot handle this yet.
    # if x < 1234:
    #     x = 0
    y = x
    #:: ExpectedOutput(call.precondition:assertion.false)
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
