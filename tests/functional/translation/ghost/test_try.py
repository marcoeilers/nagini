# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Ghost
def gfunc() -> int:
    pass

def regular_try(x: int) -> int:
    gi: GInt = 0
    try:
        gi = gfunc()
        x = x + 1
    except Exception:
        x = 2
    finally:
        gi = gfunc()
    return x
