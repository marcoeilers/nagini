from abc import ABC
from nagini_translation.native.vf.standard.value import ValueT

from typing import Generic

#any expression must return a value in the end...
class Expr(ABC, Generic[ValueT]):
    def getType(self):
        pass
