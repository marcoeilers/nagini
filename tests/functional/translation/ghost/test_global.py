# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


g_counter: GInt = 0
r_counter: int = 0


def use_regular() -> int:
    return r_counter

@Ghost
def use_ghost() -> int:
    return g_counter
