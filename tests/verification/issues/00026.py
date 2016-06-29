#:: IgnoreFile(/py2viper/issue/30/)
from py2viper_contracts.contracts import *
from typing import Tuple


def test(a: int, b: int) -> Tuple[int, int]:
    Ensures(
        #:: UnexpectedOutput(postcondition.violated:assertion.false, /py2viper/issue/26/)
        ((True and
        True) and
        True) and
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        #:: MissingOutput(postcondition.violated:assertion.false, /py2viper/issue/26/)
        (Result()[0] == a and
        Result()[1] == b)
        )
    return b, a
