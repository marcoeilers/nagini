from abc import ABC
from nagini_translation.native.vf.standard.value import Value

class Literal(ABC, Value):
    pass


class int(Literal):
    pass

class float(Literal):
    pass

class ptr(Literal):
    pass


