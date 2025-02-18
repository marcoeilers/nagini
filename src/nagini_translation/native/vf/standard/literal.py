from abc import ABC
from nagini_translation.native.vf.standard.value import Value


class Literal(Value, ABC):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Int(Literal):
    pass

class Bool(Literal):
    pass

class Float(Literal):
    pass


class Ptr(Literal):
    pass


class Char(Literal):
    pass
