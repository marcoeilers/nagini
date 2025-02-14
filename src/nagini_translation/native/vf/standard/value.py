from nagini_translation.native.vf.standard.expr import Expr
from typing import TypeVar
from typing import Type

from abc import ABC

class Value(Expr, ABC):
    pass

class ValueLocation:
    def __init__(self, type: Type[Value]):
        self.__content = None
        self.__type = type

    def setContent(self, content: Expr):
        # TODO check that the content matches location type
        self.__content = content

    def getContent(self):
        return self.__content
class Wildcard(Value):
    def __init__(self):
        pass
    def __str__(self) -> str:
        pass

ValueT = TypeVar("ValueT", bound="Value")

