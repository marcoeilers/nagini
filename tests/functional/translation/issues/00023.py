#:: IgnoreFile(/py2viper/issue/23/)
from py2viper_contracts.contracts import *
from typing import Tuple


def bla() -> Tuple[int, str]:
    Ensures(Result()[0] == "bla" and Result()[1] == 2)
    return 2, "bla"
