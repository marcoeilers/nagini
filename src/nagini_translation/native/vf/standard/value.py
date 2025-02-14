from nagini_translation.native.vf.standard.expr import Expr
from typing import TypeVar, Generic

from abc import ABC

ValueT = TypeVar("ValueT", bound="Value")
class Value(Expr, ABC):
    pass
class ValueLocation(Generic[ValueT]):
    def __init__(self):
        self.__content = None

    def setContent(self, content: Expr[ValueT]):
        # TODO check that the content matches location type
        self.__content = content

    def getContent(self):
        return self.__content
class Wildcard(Value):
    def __init__(self):
        pass
    def __str__(self) -> str:
        pass


