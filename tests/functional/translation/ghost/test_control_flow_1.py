# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import List

GInt = int
MarkGhost(GInt)

def main(i: int, gi: GInt) -> None:
    if i == 0: 
        i = 1
        gi = 0
    
    if gi == 0:
        gi = 1
    
    if i > 0:
        i += 1
        if gi != 5:
            gi = 0
        else:
            if i >= 2:
                gi = 6

    while i < 2:
        i += 1
        gi += 1
    
    while i < 5:
        i += 1
        if i == 4:
            break
        continue

    lst = [1,1]
    for x in lst:
        i += x
        gi += x

    glst: List[GInt] = lst
    for y in glst:
        gi += y