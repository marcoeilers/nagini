#:: IgnoreFile(/py2viper/issue/28/)
from py2viper_contracts.contracts import *
from typing import Tuple


@GhostReturns(2)
def test() -> Tuple[int, int, int]:
    return 1, 2, 3
