from abc import ABC
from typing import Tuple, TypeVar, Generic
from nagini_translation.native.vf.standard.expr import Expr
from nagini_translation.native.vf.standard.value import Value


class Fact(ABC):
    pass


class BooleanFact(Fact):  # a fact built using any boolean ast.expression
    pass


_T = TypeVar("T", bound=Tuple[Value, ...])


class PredicateFact(Fact, ABC):  # a fact built using a predicate
    pass


class FactConjunction(Fact):
    def __init__(self, f: list[Fact]):
        self.f = f

    def __str__(self) -> str:
        return " &*&\n".join(map(str, self.f))
