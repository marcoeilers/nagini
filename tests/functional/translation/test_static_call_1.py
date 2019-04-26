# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class A:

    def first(self) -> int:
        #:: ExpectedOutput(invalid.program:recursive.static.call)
        return A.second(self)

    def second(self) -> int:
        return A.first(self)