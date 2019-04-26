# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


#:: ExpectedOutput(invalid.program:function.dead.code)
@Pure
def f1(i: int) -> int:
    a = i + 67
    return a - 34
    return 23 - 45
