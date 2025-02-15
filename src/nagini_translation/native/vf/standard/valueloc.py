from typing import TypeVar, Generic
from nagini_translation.native.vf.standard.expr import Expr
from nagini_translation.native.vf.standard.value import Value

ValueT = TypeVar("ValueT", bound="Value")


class ValueLocation(Generic[ValueT]):
    def __init__(self):
        self.__content = None

    def setContent(self, content: Expr[ValueT]):
        # TODO check that the content matches location type
        self.__content = content

    def getContent(self):
        return self.__content
