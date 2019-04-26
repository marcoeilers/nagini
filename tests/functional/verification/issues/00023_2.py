# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def bla() -> Tuple[int, str]:
    #:: ExpectedOutput(application.precondition:assertion.false)|ExpectedOutput(carbon)(postcondition.violated:assertion.false)|UnexpectedOutput(carbon)(application.precondition:assertion.false, 168)|UnexpectedOutput(carbon)(postcondition.violated:assertion.false, 168)
    Ensures(Result()[0] == "bla" and Result()[1] == 2)
    return 2, "bla"
