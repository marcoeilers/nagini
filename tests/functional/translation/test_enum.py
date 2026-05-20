# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from enum import IntEnum

class flag(IntEnum):
    success = 0
    failure = 1

#:: ExpectedOutput(invalid.program:Cannot extend enumeration)
class sub_flag(flag):
    unknown = 3