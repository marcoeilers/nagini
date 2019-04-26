# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.adt import ADT
from typing import NamedTuple

# 2 - Other class instead of NamedTuple
class ADT_2(ADT):
    pass

class NotNamedTuple:
    pass

#:: ExpectedOutput(invalid.program:malformed.adt)
class ADT_2_Cons(ADT_2, NotNamedTuple):
    pass
