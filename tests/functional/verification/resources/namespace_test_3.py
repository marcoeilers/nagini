# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Predicate
def P(i: int) -> bool:
    return i == 2


@Pure
def a_function() -> bool:
    return True