from abc import ABC
from nagini_translation.native.vf.standard.value import Value

class Literal(Value, ABC):
    pass


class Int(Literal):
    pass

class Float(Literal):
    pass

class Ptr(Literal):
    pass


