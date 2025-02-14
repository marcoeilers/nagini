from abc import ABC
from nagini_translation.native.vf.standard.value import ValueT
from typing import Generic

class Expr(ABC, Generic[ValueT]):
    # any expression must return a value in the end...
    pass
