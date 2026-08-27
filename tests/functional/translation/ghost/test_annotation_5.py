# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

import resources.test_ghost_import_file as ghost_import
from resources.test_ghost_import_file import GBoolList


def qualified_argument(l: ghost_import.GBoolList) -> GInt:
    # The argument is ghost, so the result of the call is ghost as well.
    return len(l)

def unqualified_argument(l: GBoolList) -> GInt:
    return len(l)
