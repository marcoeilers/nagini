# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

@Pure
def to_bool(val: object) -> bool:
    return bool(val)

def test() -> None:
    b = False
    b2 = to_bool(b)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert b2 == True