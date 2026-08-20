# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

@Pure
def f(n: int) -> int:
    Requires(n >= 0)
    Decreases(n)
    if n == 0:
        return 0
    else:
        m: int = n - 1
        return f(m) + 1