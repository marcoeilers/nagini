# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

# 4 - Too many superclasses
class ADT_4(ADT):
    pass

class AnySuperClass:
    pass

#:: ExpectedOutput(invalid.program:malformed.adt)
class ADT_4_Cons(ADT_4, NamedTuple('ADT_4_Cons', []), AnySuperClass):
    pass
