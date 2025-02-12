from abc import ABC, abstractmethod
import typing
import ast


class pred(ABC):
    def __init__(self, name: str):
        self.name = name



class Fact(ABC):
    pass


class ValDef(ABC):
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


class FromArgs(ValDef):
    def __str__(self) -> str:
        raise NotImplementedError()
        return self.name


class Pattern(ast.expr, ValDef):
    def __init__(self, name: str):
        ValDef.__init__(self, name)
        self.fact = None
    def __str__(self) -> str:
        return "?"+self.name


class VFVal(ast.expr):
    def __init__(self, definition: ValDef):
        self.definition = definition

    def __str__(self) -> str:
        return str(self.definition.name)


class PredicateFact(Fact, ABC):  # a fact built using a predicate
    def __init__(self, pred: pred, args: list[ast.expr]):
        self.args = args
        self.pred = pred

    def __str__(self) -> str:
        return self.pred.name + "(" + ", ".join(map(str, self.args)) + ")"


class BooleanFact(Fact):  # a fact built using any boolean ast.expression
    def __init__(self, pureBoolean: ast.expr):
        self.pureBoolean = pureBoolean

class FactConjunction(Fact):
    def __init__(self, f: list[Fact]):
        self.f = f

    def __str__(self) -> str:
        return " &*&\n".join(map(str, self.f))


class PyObj_v(ast.expr):
    def __init__(self, vf: ast.expr):
        self.vf = vf
