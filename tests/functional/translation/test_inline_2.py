# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
@Inline  #:: ExpectedOutput(invalid.program:decorators.incompatible)
def test1() -> int:
    return 5