# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def specialVals() -> None:
    nan = float("nan")
    nf = float("inF")
    one = float("1.0")
    Assert(nf > one)
    Assert(not nan == nan)
    Assert(nan == nan)
