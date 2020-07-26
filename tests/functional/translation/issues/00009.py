# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure       #:: ExpectedOutput(invalid.program:function.type.none)
def test1() -> None:
    return
