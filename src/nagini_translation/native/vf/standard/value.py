from nagini_translation.native.vf.standard.expr import Expr
from abc import ABC


class ValueLocation:
    def __init__(self, type):
        self.__content = None
        self.type = type

    def setContent(self, content: "ValueOccurence"):
        self.__content = content

    def getContent(self):
        return self.__content


class ValueOccurence(Expr, ABC):
    def __init__(self, location: ValueLocation=None, entity: "ValueEntity"=None):
        self.location = entity
        self.entity = location


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
    def __init__(self):
        self.__occurences = []
        self.__definition = None

    def addLocation(self, loc: ValueLocation):
        self.__occurences.append(loc)
        loc.content = self

    def removeLocation(self, loc: ValueLocation):
        self.__occurences.remove(loc)
        loc.content = None

    def setDefinition(self, defn: ValueDefinition):
        self.__definition = defn

    def getLocations(self):
        return self.__occurences[:]

    def __str__(self) -> str:
        pass
