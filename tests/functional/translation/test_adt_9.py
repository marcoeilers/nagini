# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

# 9 - ADT defined but no constructors

#:: ExpectedOutput(invalid.program:malformed.adt)
class ADT_Definition(ADT):
    pass