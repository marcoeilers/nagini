# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

from resources.test_ghost_import_file import GBoolList as ImportedGBoolList, ghost_func
import resources.test_ghost_import_file as ghost_import


def imported_alias(b: GBool) -> ImportedGBoolList:
    return [b]

def other_alias_import(b: GBool) -> ghost_import.GBoolList:
    return [b]

@Ghost
def imported_func() -> None:
    gi = 0
    loc = ghost_func(gi)
