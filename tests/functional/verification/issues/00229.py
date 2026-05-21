# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# Pure functions with a missing return on some branch were silently accepted
# before this fix; the translator dropped the guard on the last return and used
# its value as a default for all paths.

from nagini_contracts.contracts import *


@Pure  #:: ExpectedOutput(function.not.wellformed:assertion.false)
def missing_return_then_branch(i: int) -> int:
    # The i > 0 branch has no return; should be rejected.
    y = 18
    if i > 0:
        y = y + 1
    elif i < 0:
        return 0
    else:
        y = y * 2
        return 3


@Pure  #:: ExpectedOutput(function.not.wellformed:assertion.false)
def missing_return_simple(i: int) -> int:
    # Only two of the three branches return; should be rejected.
    if i > 0:
        y = 1
    elif i < 0:
        return 0
    else:
        return 3


@Pure
def all_branches_return(i: int) -> int:
    # All three branches return; should be accepted.
    if i > 0:
        return 1
    elif i < 0:
        return -1
    else:
        return 0


@Pure
def missing_return_made_unreachable(i: int) -> int:
    # The missing-return path is ruled out by the precondition; should be accepted.
    Requires(i > 0)
    if i > 0:
        return i
