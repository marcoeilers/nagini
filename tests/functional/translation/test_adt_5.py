# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

# 5 - Attempt to define a constructor directly from ADT
#     without defining first an ADT class

#:: ExpectedOutput(invalid.program:malformed.adt)
class Constructor(ADT, NamedTuple('Constructor', [('elem', int)])):
    pass
