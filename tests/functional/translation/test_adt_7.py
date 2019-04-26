# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

# 7 - Attempt to subclass an ADT constructor class

class ADT_Definition(ADT):
    pass

class Constructor(ADT_Definition, NamedTuple('Constructor',[])):
    pass

#:: ExpectedOutput(invalid.program:malformed.adt)
class WrongSubclass(Constructor):
    pass