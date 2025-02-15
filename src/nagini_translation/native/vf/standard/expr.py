from abc import ABC
from nagini_translation.native.vf.standard.value import Value
from typing import Generic
from typing import TypeVar

ValueT = TypeVar("ValueT", bound="Value")
class Expr(ABC, Generic[ValueT]):
    # any expression must return a value in the end...
    pass
