# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SomeClass:

    @Predicate      #:: ExpectedOutput(invalid.program:invalid.predicate)
    def meh(self, val: int) -> int:
        return val