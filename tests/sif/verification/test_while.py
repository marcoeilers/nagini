from py2viper_contracts.contracts import *
from sif_utils import input_high, input_low, sif_print


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
        Invariant(Low(sum))
        sum = sum + 1
        i = i - 1
    sif_print(sum)
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
    """While with pure guard."""
    Requires(Low())
    Ensures(Result() == 10)
    i = 15
    sum = 0
    while m1(i):
        Invariant(sum == 15 - i)
        Invariant(Low(i))
        Invariant(Low(sum))
        sum = sum + 1
        i = i - 1
    sif_print(sum)
    return sum