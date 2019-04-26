# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


#:: ExpectedOutput(invalid.program:function.return.missing)
@Pure
def some_func(a: bool, b: int) -> bool:
    c = b == 56
    d = a and c
