# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


#:: ExpectedOutput(invalid.program:invalid.predicate)
@Predicate
def meh(val: int) -> int:
    return val