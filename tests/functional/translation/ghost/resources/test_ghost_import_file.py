# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

GBool = bool
MarkGhost(GBool)

@Ghost
def ghost_func(i: int) -> int:
    return i
