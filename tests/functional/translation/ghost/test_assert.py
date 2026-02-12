# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main() -> None:
    gi: GInt = 0
    #:: ExpectedOutput(invalid.program:invalid.ghost.assert)
    assert gi == 0
