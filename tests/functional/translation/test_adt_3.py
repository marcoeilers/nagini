from nagini_contracts.adt import ADT
from typing import NamedTuple

# 3 - Unmatching name in NamedTuple
class ADT_3(ADT):
    pass

#:: ExpectedOutput(invalid.program:malformed.adt)
class ADT_3_Cons(ADT_3, NamedTuple('DifferentName', [])):
    pass
