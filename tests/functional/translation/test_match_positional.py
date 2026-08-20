# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Point:
    __match_args__ = ('x', 'y')

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def match_positional(p: Point) -> int:
    Requires(Acc(p.x) and Acc(p.y))

    match p:  #:: ExpectedOutput(unsupported:positional class patterns not yet supported)
        case Point(x, y):
            return x + y
        case _:
            return 0
