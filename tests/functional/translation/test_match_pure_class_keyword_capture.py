# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Point:
    def __init__(self, x: int) -> None:
        self.x = x
        Ensures(Acc(self.x) and self.x == x)


@Pure
def pure_match_class_keyword_capture(p: Point) -> int:
    Requires(Acc(p.x))
    Ensures(Result() == p.x)
    match p:  #:: ExpectedOutput(unsupported:class patterns with parameters not yet supported)
        case Point(x=y):
            return y
        case _:
            return 0
