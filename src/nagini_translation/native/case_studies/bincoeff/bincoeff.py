from nagini_contracts.contracts import *

@Pure
def bincoeff(VALUEONLY_n: int, VALUEONLY_k: int) -> int:
    Requires(VALUEONLY_n >= 0 and VALUEONLY_k >= 0 and VALUEONLY_n >= VALUEONLY_k)
    if VALUEONLY_k == 0:
        return 1
    elif(VALUEONLY_n == VALUEONLY_k):
        return 1
    else:
        return bincoeff(VALUEONLY_n - 1, VALUEONLY_k - 1) + bincoeff(VALUEONLY_n - 1, VALUEONLY_k)
@ContractOnly
@Native
def compute_bincoeff(n: int, k: int) -> None:
    Requires(n >= 0 and k >= 0 and k <= n and n <= 63)
    Ensures(Result() == bincoeff(n, k))