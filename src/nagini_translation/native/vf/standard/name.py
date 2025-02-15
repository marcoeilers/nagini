
from abc import ABC
from nagini_translation.native.vf.standard.value import Value
from nagini_translation.native.vf.standard.valueloc import ValueLocation
from nagini_translation.native.vf.standard.expr import Expr
from typing import Generic

from typing import TypeVar
_ValueT = TypeVar("_ValueT", bound="Value")

# DEFINITION: a name is an annotation-internal variable that is used to refer to a value.


class NameOccurence(Expr, ABC, Generic[_ValueT]):
    def __init__(self, location: ValueLocation = None, entity: "NamedValue" = None):
        self.__location = location
        self.__entity = entity
        entity.addLocation(location)


class NameDefinition(NameOccurence, Generic[_ValueT]):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class NameUse(NameOccurence, Generic[_ValueT]):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class NamedValue(Generic[_ValueT]):
    def __init__(self,  name: str):
        self.__occurences = []
        self.__def = None
        self.__name = str

    def getName(self):
        return self.__name

    def addLocation(self, loc: ValueLocation[_ValueT]):
        # TODO check that the location matches entity type
        self.__occurences.append(loc)
        loc.setContent(self)

    def removeLocation(self, loc: ValueLocation[_ValueT]):
        self.__occurences.remove(loc)
        loc.content = None

    def setDef(self, defn: ValueLocation[_ValueT]):
        # TODO check that the location matches entity type
        self.__def = defn

    def getDef(self):
        return self.__def

    def getLocations(self):
        return self.__occurences[:]

    def __str__(self) -> str:
        pass
