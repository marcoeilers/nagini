# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
@Pure
def first(s: PSeq[int]) -> int:
    Requires(len(s) > 0)
    if len(s) == 1:
        return s[0]
    else:
        return first(s.drop(1))


def use_in_ghost_code(s: PSeq[int]) -> None:
    Requires(len(s) > 0)
    gi: GInt = first(s)
    Assert(gi == first(s))
