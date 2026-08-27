# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def assign_ghost_to_regular(gi: GInt) -> int:
    i = gi  # NOTE: ghost/test_import_2.py expects the error on this line.
    return i
