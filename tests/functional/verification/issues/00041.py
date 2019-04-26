# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


#:: ExpectedOutput(postcondition.violated:assertion.false)
def test1() -> Tuple[int, int]:
    pass
