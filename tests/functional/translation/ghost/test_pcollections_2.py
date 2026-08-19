# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def seq_to_regular(s: PSeq[int]) -> int:
    # The length of a ghost sequence is ghost as well.
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    i = len(s)
    return i
