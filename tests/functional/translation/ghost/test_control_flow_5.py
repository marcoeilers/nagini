# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List


def main(i: int, glst: List[GInt]) -> None:
    for y in glst:
        #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
        i += 1
