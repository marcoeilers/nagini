# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# A static field is to a class what a global variable is to a module, so a
# method may no more share its name than a function may share the name of a
# global.
class Outer:
    x = 1

    #:: ExpectedOutput(invalid.program:multiple.definitions)
    def x(self) -> int:  # type: ignore
        Ensures(Result() == 2)
        return 2
