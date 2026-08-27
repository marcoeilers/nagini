# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


@ContractOnly
def declared(x: int, gi: GInt) -> Tuple[int, GInt]:
    Requires(x > 0)
    Ensures(Result()[0] > 0)

def client(x: int) -> int:
    Requires(x > 0)
    gi: GInt = 0
    r, gi = declared(x, gi)
    return r
