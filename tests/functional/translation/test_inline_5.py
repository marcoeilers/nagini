# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Inline
def test1() -> int:
    #:: ExpectedOutput(invalid.program:contract.in.inline.method)
    Ensures(Result() > 0)
    return 6