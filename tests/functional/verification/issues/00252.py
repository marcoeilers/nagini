# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# Pure functions did not check whether read variables had been previously
# defined.  The fix uses _assuming/_checkDefined to enforce definedness at
# the expression level, mirroring the inhale/_checkDefined mechanism used
# in impure functions.

from nagini_contracts.contracts import *


@Pure
def pure_unconditional_assign_ok(x: int) -> int:
    # Always assigns y before reading it; should be accepted.
    Ensures(Result() == x + 1)
    y = x + 1
    return y


@Pure
def pure_cond_assign_all_branches_ok(x: int) -> int:
    # Both branches assign y; should be accepted.
    Ensures(Result() >= 0)
    if x > 0:
        y = 1
    else:
        y = 0
    return y


@Pure
def pure_cond_assign_missing_branch(x: int) -> int:
    # Only the then-branch assigns y; should be rejected.
    if x > 0:
        y = 1
    #:: ExpectedOutput(expression.undefined:undefined.local.variable)
    return y


@Pure
def pure_precond_makes_branch_reachable(x: int) -> int:
    # Precondition guarantees x > 0, so y is always assigned; should be accepted.
    Requires(x > 0)
    Ensures(Result() == 1)
    if x > 0:
        y = 1
    return y
