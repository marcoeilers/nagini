# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List, Tuple

GInt = int
MarkGhost(GInt)

def reg_calls(gi: GInt) -> None:
    i = reg(0, gi)
    gi = ghost(0)
    gi = ghost(reg(0, 0))
    gi = reg_but_ghost_return()
    gi = ghost_lst([0, 1, ghost(reg(2,2)), 3])
    
    gk: GInt = 0
    r, (gi, gk) = reg_mixed_return()
    g_tuple: Tuple[Tuple[GInt, GInt], Tuple[GInt, GInt]] = reg_mixed_return()

    i = reg(*r)

    lst = [pure_reg(e) for e in [0, 1, 2]]

    str_lst = "one two".split(' ')

@Ghost
def ghost_calls(lst: List[int]) -> None:
    gi = ghost(0)
    gi = ghost_lst([0, 1, ghost(2), 3])
    
    g_lst = [pure_ghost(e) for e in lst]

def reg(i: int, gi: GInt) -> int:
    # Do something with potential side-effects
    pass

def reg_but_ghost_return() -> GInt:
    pass

def reg_mixed_return() -> Tuple[Tuple[int, int], Tuple[GInt, GInt]]:
    pass

@Pure
def pure_reg(i: int) -> int:
    return i+1

@Ghost
def ghost(i: int) -> int:
    pass

@Ghost
def ghost_lst(lst: List[int]) -> int:
    pass

@Ghost
@Pure
def pure_ghost(i: int) -> int:
    return i+1