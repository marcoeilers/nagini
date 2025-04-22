from nagini_contracts.contracts import *

@Pure
def bincoeff(VALUEONLY_n: int, VALUEONLY_k: int) -> int:
    Requires(VALUEONLY_n >= 0 and VALUEONLY_k >= 0)
    if VALUEONLY_k == 0 or VALUEONLY_n == VALUEONLY_k:
        return 1
    else:
        return bincoeff(VALUEONLY_n - 1, VALUEONLY_k - 1) + bincoeff(VALUEONLY_n - 1, VALUEONLY_k)