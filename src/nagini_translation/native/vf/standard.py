
class expr:
    pass


class pred:
    def __init__(self, name: str):
        self.args_nr = name


class ptr(expr):
    pass


class pair(expr):
    def __init__(self, e1: expr, e2: expr):
        self.e1 = e1
        self.e2 = e2


class fact:
    pass


class fact_pred(fact):  # a fact built using a predicate
    def __init__(self, pred: pred, args: list[expr]):
        self.args = args
        self.pred = pred


class fact_comparison(fact):  # a fact built using a comparison
    def __init__(self, e1: expr, e2: expr, op: str):
        self.e1 = e1
        self.e2 = e2


class statement():
    def __init__(self, f: list[fact]):
        self.f = f

    def __str__(self) -> str:
        return " &*&\n".join(map(str, self.f))


class PyObj_v(expr):
    def __init__(self, vf: expr):
        self.vf = vf
