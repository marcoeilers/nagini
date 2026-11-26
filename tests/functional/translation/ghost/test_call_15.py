# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Union

from nagini_contracts.contracts import *


class A:
    def bump(self) -> int:
        return 1


class B:
    def bump(self) -> int:
        return 1


class Table:
    item = 0

    @Ghost
    def ghost_call(self, item: Union[A, B]) -> None:
        # The receiver is the parameter, not the class attribute of that name.
        #:: ExpectedOutput(invalid.program:invalid.ghost.call)
        x = item.bump()
