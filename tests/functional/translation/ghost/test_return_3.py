# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


def single_element_tuple(i: int) -> Tuple[int]:
    return (i,)

def regular_tuple(i: int) -> Tuple[int, int]:
    return i, i

def ghost_tuple(gi: GInt) -> Tuple[GInt, GInt]:
    return gi, gi

def mixed(i: int, gi: GInt) -> Tuple[int, GInt]:
    return i, gi

def forward_mixed(i: int, gi: GInt) -> Tuple[int, GInt]:
    # Returning the result of a call with an equivalent return type is fine.
    return mixed(i, gi)
