# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

from typing import cast

def add_zero(i: int, secret: int) -> int:
    Requires(Low(i))
    Ensures(LowVal(Result()))
    if secret == 0:
        return i + 0
    return i