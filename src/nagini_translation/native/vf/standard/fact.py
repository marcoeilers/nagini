from abc import ABC
from typing import Tuple, TypeVar, Generic
from nagini_translation.native.vf.standard.expr import Expr
from nagini_translation.native.vf.standard.value import Value
from nagini_translation.native.vf.standard.literal import Bool
from fractions import Fraction
_BoolT = TypeVar("ValueT", bound="Bool")


class Fact(ABC):
    pass


class BooleanFact(Fact):  # a fact built using any boolean ast.expression
    def __init__(self, e: Expr[_BoolT]):
        self.e = e

    def __str__(self) -> str:
        return str(self.e)


class PredicateFact(Fact, ABC):
    # a fact built using a predicate
    # (user must create subclasses to instantiate)
    def __init__(self, name, *args, frac=Fraction(1)):
        self.name = name
        self.args = args
        self.frac = frac
    def __str__(self):
        fracstr = "["+str(self.frac.numerator)+"/"+str(self.frac.denominator)+"]" if self.frac != Fraction(1) else ""
        return f"{fracstr}{self.name}({', '.join(map(str, self.args))})"

class NaginiPredicateFact(PredicateFact):
    pass

class FactConjunction(Fact):
    def __init__(self, f: list[Fact]):
        self.f = f

    def __str__(self) -> str:
        return " &*&\n".join(map(str, self.f))


class TernaryFact(Fact):
    def __init__(self, cond: Expr[_BoolT], then: Fact, orelse: Fact):
        self.cond = cond
        self.then = then
        self.orelse = orelse

    def __str__(self) -> str:
        return f"{self.cond} ? (\n{self.then}) : (\n{self.orelse})"
