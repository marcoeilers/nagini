# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


#:: ExpectedOutput(exhale.failed:assertion.false)
def test1() -> None:
    raise Exception()
