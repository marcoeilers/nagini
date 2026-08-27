# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def impure(i: int) -> int:
    pass


def main() -> None:
    # Removing the ghost statement would remove the effect of the call, so
    # impure functions may not be called in ghost code.
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    Assert(impure(3) == 3)
