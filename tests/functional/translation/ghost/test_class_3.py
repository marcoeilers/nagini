# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

@Ghost
class GhostClass:
    pass

#:: ExpectedOutput(invalid.program:invalid.ghost.classDef)
class RegClass(GhostClass):
    pass