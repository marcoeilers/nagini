# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# Classes nested in other classes are supported, classes declared inside a
# function are not.
def declare_class() -> None:
    #:: ExpectedOutput(invalid.program:nested.class.declaration)
    class Local:
        pass
