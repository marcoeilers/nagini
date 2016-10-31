from py2viper_contracts.contracts import *


# Helper functions to generate high/low input.
# TODO(shitz): Move to common utils file when imports are properly supported.
def input_high() -> int:
    return 42


def input_low() -> int:
    Requires(Low())
    Ensures(Low(Result()))
    return 42


def sif_print(x: int) -> None:
    Requires(Low(x))
    pass


def test(x: int) -> bool:
    Ensures(Result() == (x > 5))
    return x > 5


def while1() -> int:
    """While with low guard."""
    Requires(Low())
    i = input_low()
    sum = 0
    while i != 0:
        Invariant(Low(i))
        sum = sum + 1
        i = i - 1

    return sum


def while2() -> None:
    """While with high guard."""
    Requires(Low())
    x = input_high()
    while x != 0:
        #:: ExpectedOutput(invariant.not.established:assertion.false)
        Invariant(Low())
        x = x - 1
    sif_print(1)


def while3() -> None:
    """Termination leak."""
    Requires(Low())
    x = input_high()
    while x != 0:
        x = x - 1
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(1)


@Pure
def m1(a: int) -> bool:
    Ensures(Result() == (a != 5))
    Ensures(Implies(Low(a), Low(Result())))
    return a != 5


def while4() -> int:
    """Purity violated."""
    Requires(Low())
    Ensures(Result() == 10)
    i = 15
    sum = 0
    Assert(Low(m1(i)))
    #:: ExpectedOutput(invalid.program:purity.violated)
    while m1(i):
        Invariant(sum == 15 - i)
        Invariant(Low(m1(i)))
        sum = sum + 1
        i = i - 1
        Assert(Low(i))
    return sum