from py2viper_contracts.contracts import Ensures, Low, Requires, Result


def input_high() -> int:
    return 42


def input_low() -> int:
    Requires(Low())
    Ensures(Low(Result()))
    return 42


def sif_print(x: int) -> None:
    Requires(Low(x))
    pass
