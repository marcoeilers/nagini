# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main(i: int, gi: GInt) -> None:
    while gi < 5:
        #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
        i += 1
