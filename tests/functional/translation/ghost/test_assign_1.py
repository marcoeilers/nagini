# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main(i: int, gi: GInt) -> None:
    j = i + 2 
    i += 1 

    res: GInt = gi + i
    gi += 1

    t = (0, 1)
    i, j = t
    gi, res = t

    lst = [0, 1, 2, 3, 4]
    i, *s, j = lst
