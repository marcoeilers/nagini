from abc import ABC, abstractmethod
import typing

class expr(ABC):
    pass


class pred(ABC):
    def __init__(self, name: str):
        self.name = name


class val_pattern(expr):
    def __init__(self, name: str):
        self.name = name
    def __str__(self) -> str:
        return "?"+self.name


class val(expr):
    def __init__(self, val: val_pattern):
        self.value = val


t1 = typing.TypeVar("t1", bound=expr)
t2 = typing.TypeVar("t2", bound=expr)
class pair(expr, typing.Generic[t1, t2]):
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

class vflist(expr):
    def __init__(self, items: list[expr]):
        self.items = items
class fact_conjunction(fact):
    def __init__(self, f:list[fact]):
        self.f=f
    def __str__(self) -> str:
        return " &*&\n ".join(map(str, self.f)) 

class PyObj_v(expr):
    def __init__(self, vf: expr):
        self.vf = vf
