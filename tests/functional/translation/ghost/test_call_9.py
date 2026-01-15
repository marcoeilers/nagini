# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Union

GInt = int
MarkGhost(GInt)

class A:
    def method(self) -> None:   # Regular Method
        pass

class B:
    @Ghost
    def method(self) -> None:    # Ghost Method
        pass

def reg_calls(u: Union[A, B]) -> None:
    #:: ExpectedOutput(invalid.program:invalid.ghost.call)
    u.method()


