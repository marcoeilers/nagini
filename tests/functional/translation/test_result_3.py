# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def noreturn() -> None:
    #:: ExpectedOutput(invalid.program:invalid.result)
    Ensures(int, lambda i: i is None)
    pass