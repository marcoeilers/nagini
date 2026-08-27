# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

import resources.test_ghost_import_file as ghost_import


def qualified_argument(l: ghost_import.GBoolList) -> int:
    # The argument does not exist at runtime, so its length is ghost.
    #:: ExpectedOutput(invalid.program:invalid.ghost.assign)
    i = len(l)
    return i
