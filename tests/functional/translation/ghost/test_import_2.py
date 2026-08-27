# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

# Imported modules are ghost checked as well. Positions are relative to the
#:: ExpectedOutput(invalid.program:invalid.ghost.assign)
from resources.test_ghost_invalid_file import assign_ghost_to_regular
# file that is verified, so the expected line above is the line of the invalid
# assignment inside resources/test_ghost_invalid_file.py.


def main(gi: GInt) -> int:
    return assign_ghost_to_regular(gi)
