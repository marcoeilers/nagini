# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SuperA:
    @Pure
    def foo(self, a: int) -> int:
        return a


# only pure and OPAQUE functions can be overridden
class SubA(SuperA):
    @Pure
    #:: ExpectedOutput(invalid.program:invalid.override)
    def foo(self, a: int) -> int:
        return a + 5