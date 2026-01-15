# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

from resources.test_ghost_import_file import GBool as ImportedGBool, ghost_func
import resources.test_ghost_import_file as ghost_import

GBool = bool
MarkGhost(GBool)

def imported_alias(b: GBool) -> ImportedGBool:
    return b

def other_alias_import(b: GBool) -> ghost_import.GBool:
    return b

@Ghost
def imported_func() -> None:
    gi = 0
    loc = ghost_func(gi)
