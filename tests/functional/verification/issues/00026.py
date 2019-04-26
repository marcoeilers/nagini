# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

#:: IgnoreFile(26)
from nagini_contracts.contracts import *
from typing import Tuple


def test(a: int, b: int) -> Tuple[int, int]:
    Ensures(
        #:: UnexpectedOutput(postcondition.violated:assertion.false, 26)
        ((True and
        True) and
        True) and
        #:: ExpectedOutput(postcondition.violated:assertion.false)|MissingOutput(postcondition.violated:assertion.false, 26)
        (Result()[0] == a and
        Result()[1] == b)
        )
    return b, a
