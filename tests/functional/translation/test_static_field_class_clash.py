# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# The same for a nested class sharing the name of a static field.
class Outer:
    x = 1

    #:: ExpectedOutput(invalid.program:multiple.definitions)
    class x:  # type: ignore
        pass
