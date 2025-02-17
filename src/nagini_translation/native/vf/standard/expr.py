from abc import ABC
from nagini_translation.native.vf.standard.value import Value
from typing import Generic, TypeVar

_ValueT = TypeVar("ValueT", bound="Value")


class Expr(ABC, Generic[_ValueT]):
    # any expression must return a value in the end...
    pass


class NameOccurence(Generic[_ValueT], ABC):
    def __init__(self, entity: "NamedValue[_ValueT]"):
        self.__entity = entity


class NameDefExpr(Expr[_ValueT], NameOccurence[_ValueT]):

    def __str__(self) -> str:
        pass


class NamedValue(Generic[_ValueT]):
    def __init__(self,  name: str):
        self.__def = None
        self.__name = str

    def getName(self):
        return self.__name

    def setDef(self, defn: NameDefExpr[_ValueT]):
        # TODO check that the location matches entity type
        self.__def = defn

    def getDef(self) -> NameDefExpr[_ValueT]:
        return self.__def

    def __str__(self) -> str:
        pass


class DefLessExpr(Expr[_ValueT], ABC):
    # definitionless expression: only uses names, no definitions
    def __init__(self, value: _ValueT):
        self.__value = value

    def __str__(self) -> str:
        pass


class NameUseExpr(NameOccurence[_ValueT], DefLessExpr[_ValueT]):
    def __str__(self) -> str:
        return str(self.__entity)


class ImmLiteral(DefLessExpr[_ValueT]):
    pass


_ValueT = TypeVar("ValueT", bound="Value")


class ImmInductive(DefLessExpr[_ValueT]):
    pass
