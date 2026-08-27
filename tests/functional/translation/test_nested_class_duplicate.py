# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# A class declared twice inside the same class is rejected, just as it is at
# module level. mypy reports this too, so the type: ignore is what makes the
# check reachable; without it the two declarations need not even share a
# member name for the duplicate to go unnoticed.
class Outer:
    class Inner:
        def first(self) -> int:
            Ensures(Result() == 1)
            return 1

    #:: ExpectedOutput(invalid.program:multiple.definitions)
    class Inner:  # type: ignore
        def second(self) -> int:
            Ensures(Result() == 2)
            return 2
