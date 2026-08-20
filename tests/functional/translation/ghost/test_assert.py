# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main() -> None:
    gi: GInt = 0
    # A plain assert is executed at runtime, so it may not talk about ghost
    # state; the Assert contract function has to be used instead.
    Assert(gi == 0)
    #:: ExpectedOutput(invalid.program:invalid.ghost.assert)
    assert gi == 0
