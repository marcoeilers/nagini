# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

@Opaque  #:: ExpectedOutput(invalid.program:decorators.incompatible)
def foo() -> int:
    return 6