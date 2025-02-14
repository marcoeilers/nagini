from abc import ABC
from nagini_translation.native.vf.standard.pred import Pred
from nagini_translation.native.vf.standard.expr import Expr

class Fact(ABC):
    pass


class BooleanFact(Fact):  # a fact built using any boolean ast.expression
    pass

class PredicateFact(Fact, ABC):  # a fact built using a predicate
    def __init__(self, pred: Pred, args: list[Expr]):
        self.args = args
        self.pred = pred

    def __str__(self) -> str:
        return self.pred.name + "(" + ", ".join(map(str, self.args)) + ")"


class FactConjunction(Fact):
    def __init__(self, f: list[Fact]):
        self.f = f

    def __str__(self) -> str:
        return " &*&\n".join(map(str, self.f))
