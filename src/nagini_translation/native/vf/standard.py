from abc import ABC, abstractmethod

class expr(ABC):
    pass


class pred(ABC):
    def __init__(self, name: str):
        self.name = name


class val_pattern(expr, ABC):
    def __init__(self, name: str):
        self.name = name
    def __str__(self) -> str:
        return "?"+self.name


class val(expr, ABC):
    def __init__(self, val: val_pattern):
        self.value = val


class pair(expr):
    def __init__(self, e1: expr, e2: expr):
        self.e1 = e1
        self.e2 = e2


class fact(ABC):
    pass


class fact_pred(fact, ABC):  # a fact built using a predicate
    def __init__(self, pred: pred, args: list[expr]):
        self.args = args
        self.pred = pred
    def __str__(self) -> str:
        return self.pred.name + "(" + ", ".join(map(str, self.args)) + ")"



class fact_comparison(fact):  # a fact built using a comparison
    def __init__(self, e1: expr, e2: expr, op: str):
        self.e1 = e1
        self.e2 = e2


class fact_conjunction(fact):
    def __init__(self, f1: fact, f2: fact):
        self.f1 = f1
        self.f2 = f2

    def __str__(self) -> str:
        return "(" + str(self.f1) + " &*& " + str(self.f2)+")"


class PyObj_v(expr):
    def __init__(self, vf: expr):
        self.vf = vf
