from nagini_contracts.adt import ADT
from typing import NamedTuple

# 6 - ADT definition can only be a subclass of ADT

class ADT_Definition(ADT):
    pass

#:: ExpectedOutput(invalid.program:malformed.adt)
class WrongADTSubclass(ADT_Definition):
    pass