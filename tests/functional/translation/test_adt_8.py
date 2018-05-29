from nagini_contracts.adt import ADT
from typing import NamedTuple

# 8 - Attempt to define a constructor class with body

class ADT_Definition(ADT):
    pass

#:: ExpectedOutput(invalid.program:malformed.adt)
class WrongADTSubclass(ADT_Definition, NamedTuple('WrongADTSubclass', [])):
    def method(self) -> None:
        pass