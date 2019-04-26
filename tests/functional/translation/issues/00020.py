# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def bla(x: int) -> None:
    Requires(True)
    Ensures(x == 5)


#:: ExpectedOutput(type.error:Name 'bla' already defined)
def bla(u: int, b: str) -> None:
    return
