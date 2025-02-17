from abc import ABC
from nagini_translation.native.vf.standard.value import Value, ValueLocation, NamedValue
from typing import Generic, TypeVar

_ValueT = TypeVar("ValueT", bound="Value")


class Expr(ABC, Generic[_ValueT]):
    # any expression must return a value in the end...
    pass


class NameOccurence(Generic[_ValueT], ABC):
    def __init__(self, location: ValueLocation = None, entity: "NamedValue[_ValueT]" = None):
        self.__location = location
        self.__entity = entity
        entity.addLocation(location)


class NameDefExpr(Expr[_ValueT], NameOccurence[_ValueT]):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class DefLessExpr(Expr[_ValueT], ABC):
    # definitionless expression: only uses names, no definitions
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class NameUseExpr(NameOccurence[_ValueT], DefLessExpr[_ValueT]):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class ImmLiteral(DefLessExpr[_ValueT]):
    def __init__(self, value: _ValueT):
        self.__value = value


class ImmInductive(DefLessExpr[_ValueT]):
    def __init__(self, value: _ValueT):
        self.__value = value
