# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def main(x: int) -> None:
    Requires(x > 10)
    Refute(not (x > 0))
    #:: ExpectedOutput(refute.failed:refutation.true)
    Refute(x > 0)
    Refute(False)
    #:: ExpectedOutput(refute.failed:refutation.true)
    Refute(True)
    Refute(False)
    if x > 0:
        r = x
    else:
        #:: ExpectedOutput(refute.failed:refutation.true)
        Refute(False)
        r = 0