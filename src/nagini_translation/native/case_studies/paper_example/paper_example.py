from nagini_contracts.contracts import *


# LONG_MIN / LONG_MAX as @Pure functions: Nagini translates these to VeriFast
# fixpoints (PURE_LONG_MIN()/PURE_LONG_MAX()), which it unfolds to the literal
# values. 
@Pure
def LONG_MIN() -> int:
    return -9223372036854775808


@Pure
def LONG_MAX() -> int:
    return 9223372036854775807


# Listing 1.3 of the ISoLA paper: the Python-level spec for the `max` function
# implemented in C in Listing 1.1. Named py_max to match the C function and to
# avoid shadowing the `max` builtin.
@ContractOnly
@Native
def py_max(a: int, b: int) -> int:
    Requires(LONG_MIN() < a and a < LONG_MAX())
    Requires(LONG_MIN() < b and b < LONG_MAX())
    Ensures(Result() is (a if a > b else b))
