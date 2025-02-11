from abc import ABC, abstractmethod
import typing


class expr(ABC):
    pass


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


class Pattern(expr, ValDef):
    def __init__(self, name: str):
        super().__init__(name)
        self.fact = None
    def __str__(self) -> str:
        return "?"+self.name


class VFVal(expr):
    def __init__(self, definition: ValDef):
        self.definition = definition

    def __str__(self) -> str:
        return str(self.definition.name)


class PredicateFact(Fact, ABC):  # a fact built using a predicate
    def __init__(self, pred: pred, args: list[expr]):
        self.args = args
        self.pred = pred

    def __str__(self) -> str:
        return self.pred.name + "(" + ", ".join(map(str, self.args)) + ")"


class BooleanFact(Fact):  # a fact built using any boolean expression
    def __init__(self, e1: expr, e2: expr, op: str):
        self.e1 = e1
        self.e2 = e2


class FactConjunction(Fact):
    def __init__(self, f: list[Fact]):
        self.f = f

    def __str__(self) -> str:
        return " &*&\n".join(map(str, self.f))


class PyObj_v(expr):
    def __init__(self, vf: expr):
        self.vf = vf
