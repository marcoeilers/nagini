# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:

    def test1(self) -> int:
        return 5

class B(A):

    @Inline  #:: ExpectedOutput(invalid.program:overriding.inline.method)
    def test1(self) -> int:
        return 6