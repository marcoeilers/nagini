# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from dataclasses import dataclass
from nagini_contracts.contracts import *
from enum import IntEnum

class Color_Enum(IntEnum):
    red = 0
    green = 1
    blue = 2
    yellow = 3

@dataclass(frozen=True)
class MyClass():
    color: Color_Enum = Color_Enum.red