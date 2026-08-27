# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
def first(s: PSeq[int]) -> int:
    Requires(len(s) > 0)
    # A regular pure function may not return a value read from ghost state.
    #:: ExpectedOutput(invalid.program:invalid.ghost.return)
    return s[0]
