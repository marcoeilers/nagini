from nagini_translation.native.vf.standard.expr import Expr
from nagini_translation.native.vf.standard.literal import Literal
from typing import Type

from abc import ABC


class ValueLocation:
    def __init__(self, type: Type[Literal]):
        self.__content = None
        self.__type = type

    def setContent(self, content: Expr):
        # TODO check that the content matches location type
        self.__content = content

    def getContent(self):
        return self.__content

#DEFINITION: a value is an annotation-internal variable
class ValueOccurence(Expr, ABC):
    def __init__(self, location: ValueLocation = None, entity: "ValueEntity" = None):
        self.__location = entity
        self.__entity = location


class Wildcard(ValueOccurence):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class ValueDefinition(ValueOccurence):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class ValueUse(ValueOccurence):
    def __init__(self):
        pass

    def __str__(self) -> str:
        pass


class ValueEntity:
    def __init__(self, type: Type[Literal], name: str):
        self.__occurences = []
        self.__def = None
        self.__type = type
        self.__name = str

    def getType(self):
        return self.__type
    
    def getName(self):
        return self.__name
    
    def addLocation(self, loc: ValueLocation):
        # TODO check that the location matches entity type
        self.__occurences.append(loc)
        loc.setContent(self)

    def removeLocation(self, loc: ValueLocation):
        self.__occurences.remove(loc)
        loc.content = None

    def setDef(self, defn: ValueDefinition):
        # TODO check that the location matches entity type
        self.__def = defn

    def getDef(self):
        return self.__def

    def getLocations(self):
        return self.__occurences[:]

    def __str__(self) -> str:
        pass
