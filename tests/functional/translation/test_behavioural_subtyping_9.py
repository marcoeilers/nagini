# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Super:
    @Pure
    def some_function(self, a: int) -> int:
        return a


class Sub(Super):

    @Pure       #:: ExpectedOutput(invalid.program:invalid.override)
    def some_function(self, a: int) -> int:
        return a
