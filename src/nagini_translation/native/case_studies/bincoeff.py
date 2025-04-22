from nagini_contracts.contracts import *

@Pure
def bincoeff(n: int, k: int) -> int:
    Requires(n >= 0)
    if k == 0 or n == k:
        return 1
    else:
        return bincoeff(n - 1, k - 1) + bincoeff(n - 1, k)