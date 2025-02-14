from abc import ABC
from nagini_translation.native.vf.standard.expr import Expr

class Literal(ABC, Expr):
    pass

class CNative(Literal, ABC):
    pass

class int(CNative):
    pass

class float(CNative):
    pass

class ptr(CNative):
    pass

class Inductive(Literal, ABC):
    pass

class list(Inductive, ABC):
    pass

class cons(list):
    pass

class nil(list):
    pass

class Pair(Literal):
    pass





