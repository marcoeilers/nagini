# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Predicate
@Inline
def test1() -> int:  #:: ExpectedOutput(invalid.program:decorators.incompatible)
    return 5