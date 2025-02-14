from abc import ABC, abstractmethod
import typing
import ast
from nagini_translation.lib.program_nodes import PythonMethod
from nagini_translation.native.vf.standard.fact import Fact, FactConjunction, BooleanFact, PredicateFact

class ValDef(ABC):
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name
class Pair(tuple):
    def __str__(self) -> str:
        return "("+str(self[0])+", "+str(self[1])+")"

class FromArgs(ValDef):
    def __str__(self) -> str:
        raise NotImplementedError()
        return self.name


class Pattern(ast.Name, ValDef):
    def __init__(self, name: str):
        ValDef.__init__(self, name)
        self.fact = None
    def __str__(self) -> str:
        return "?"+self.name


class VFVal(ast.Name):
    def __init__(self, definition: ValDef):
        self.definition = definition
        #TODO: what is this useful for?
        #super().__init__(definition.name)

    def __str__(self) -> str:
        return str(self.definition.name)

class VFPredicate(PythonMethod, ABC):
    pass





class PyObj_v(ast.expr):
    def __init__(self, vf: ast.expr):
        self.vf = vf
