# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def a() -> None:
    #:: ExpectedOutput(invalid.program:nested.function.declaration)
    def b() -> None:
        return
    return