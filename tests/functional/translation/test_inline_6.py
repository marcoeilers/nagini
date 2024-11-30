# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Inline
def test1(i: int) -> int:
    Requires(i > 0)  #:: ExpectedOutput(invalid.program:contract.in.inline.method)
    return 6