# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Predicate      #:: ExpectedOutput(invalid.program:invalid.predicate)
def test1() -> None:
    return
