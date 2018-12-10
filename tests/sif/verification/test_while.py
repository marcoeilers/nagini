from nagini_contracts.contracts import *
from resources.sif_utils import input_high, input_low, sif_print


def test(x: int) -> bool:
    Ensures(Result() == (x > 5))
    return x > 5


def while1() -> int:
    """While with low guard."""
    Requires(LowEvent())
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
    Requires(LowEvent())
    x = input_low()
    while x != 0:
        x = x - 1
    sif_print(1)


def while3() -> None:
    """Termination leak."""
    x = input_high()
    while x != 0:
        x = x - 1
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(1)


@Pure
def m1(a: int) -> bool:
    Ensures(Result() == (a != 5))
    return a != 5


def while4() -> int:
    """While with pure guard."""
    Requires(LowEvent())
    Ensures(Result() == 10)
    i = 15
    sum = 0
    while m1(i):
        Invariant(sum == 15 - i)
        Invariant(Low(i))
        Invariant(Low(m1(i)))
        Invariant(Low(sum))
        sum = sum + 1
        i = i - 1
    sif_print(sum)
    return sum


def while5() -> None:
    """Nested while."""
    h = input_high()
    l = input_low()
    i = 0
    while l != 0:
        while h != 0:
            i = i + 1
            h = h -1
        l = l - 1
    #:: ExpectedOutput(call.precondition:assertion.false)
    sif_print(i)
