from nagini_contracts.contracts import Ensures, Low, LowEvent, Requires, Result


def input_high() -> int:
    return 42


def input_low() -> int:
    # Requires(Low())
    Ensures(Low(Result()))
    return 42


def sif_print(x: int) -> None:
    Requires(LowEvent())
    Requires(Low(x))
    pass
